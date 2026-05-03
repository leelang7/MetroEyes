"""CO₂ ↔ 인원 상관 검증 — IDEA-3 Weak Supervision 명분 정량화.

원래 계획: 지하역사 CO₂ ↔ 차내 인원 → BEV 모델 자기지도 학습 신호.
현실: IndoorAirQualityMeasureService API ERROR-500 (메모리). 가용 데이터는 자치구 *야외* 시간당 대기.

본 스크립트는 *약한 신호* 입증으로 후퇴:
  자치구 야외 대기 시간대 변동 ↔ 지하철 시간대 통행 변동.
  핵심 가설: 사람 활동 ↑ → 차량/배출/난방 ↑ → 야외 PM/NO₂ ↑.
  = 지하 CO₂ 못 받아도 "환경 신호 ↔ 인구 흐름" 원리 입증.

산출물:
  outputs/co2_correlation_report.json
  outputs/co2_correlation.png (matplotlib)
"""
from __future__ import annotations

import io
import json
import sys

# Windows cp949 콘솔에서 한글/유니코드 출력 안전.
if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs"
OUT_DIR.mkdir(exist_ok=True)


def load_air() -> pd.DataFrame:
    df = pd.read_parquet(ROOT / "data/processed/air_202602.parquet")
    df["dt"] = pd.to_datetime(df["MSRMT_DT"], format="%Y%m%d%H%M")
    df["hour"] = df["dt"].dt.hour
    return df


def load_subway() -> pd.DataFrame:
    df = pd.read_parquet(ROOT / "data/processed/subway_time_202602.parquet")
    return df


def hourly_subway_pattern(sw: pd.DataFrame) -> np.ndarray:
    """24시간 통행(승+하차) 평균 — 도시 전체 합산 후 정규화."""
    hours = list(range(24))
    on = [sw.get(f"HR_{h}_GET_ON_NOPE", pd.Series([0])).sum() for h in hours]
    off = [sw.get(f"HR_{h}_GET_OFF_NOPE", pd.Series([0])).sum() for h in hours]
    total = np.array(on) + np.array(off)
    if total.max() == 0:
        return total
    return total / total.max()


def hourly_air_pattern(air: pd.DataFrame, col: str) -> np.ndarray:
    """24시간 자치구 평균 → 정규화."""
    by_h = air.groupby("hour")[col].mean()
    arr = np.array([by_h.get(h, np.nan) for h in range(24)])
    if np.nanmax(arr) == 0 or np.isnan(arr).all():
        return arr
    return arr / np.nanmax(arr)


def correlate_pollutant(sub_pat: np.ndarray, air_pat: np.ndarray) -> dict:
    mask = ~(np.isnan(sub_pat) | np.isnan(air_pat))
    if mask.sum() < 5:
        return {"r": None, "p": None, "n": int(mask.sum())}
    r, p = pearsonr(sub_pat[mask], air_pat[mask])
    return {"r": float(r), "p": float(p), "n": int(mask.sum())}


def maybe_plot(sub_pat, results: dict, save: Path) -> None:
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for name in ("Malgun Gothic", "NanumGothic", "Noto Sans CJK KR"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break
    except ImportError:
        return
    hours = np.arange(24)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(hours, sub_pat, "k-", linewidth=2.5, label="지하철 통행 (정규화)")
    colors = {"NTDX": "C0", "FPM": "C1", "PM": "C2",
              "CBMX": "C3", "OZON": "C4"}
    label_kr = {"NTDX": "NO₂", "FPM": "PM2.5", "PM": "PM10",
                "CBMX": "CO", "OZON": "O₃"}
    for col, info in results.items():
        ax.plot(hours, info["pattern"], colors.get(col, "C5"),
                linewidth=1.3, alpha=0.7,
                label=f"{label_kr.get(col, col)} (r={info['r']:.2f})")
    ax.set_xlabel("시간 (0~23)")
    ax.set_ylabel("정규화 진폭")
    ax.set_title("지하철 통행 ↔ 야외 대기 시간대 상관")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)
    ax.set_xticks(range(0, 24, 2))
    plt.tight_layout()
    plt.savefig(save, dpi=120)
    print(f"  >> 그래프: {save}")


def main() -> None:
    print("CO₂ ↔ 인원 상관 검증 (IDEA-3)")
    print("=" * 60)
    print("  [!] 지하역사 CO₂ 미가용 (IndoorAir API ERROR-500)")
    print("  → 자치구 *야외* 대기 시간대 변동으로 weak signal 입증")

    air = load_air()
    sw = load_subway()
    sub_pat = hourly_subway_pattern(sw)

    cols = ["NTDX", "OZON", "CBMX", "SPDX", "PM", "FPM"]
    results = {}
    print("\n=== 시간대 상관 (Pearson r, p-value) ===")
    for col in cols:
        air_pat = hourly_air_pattern(air, col)
        cor = correlate_pollutant(sub_pat, air_pat)
        results[col] = {**cor, "pattern": air_pat.tolist()}
        sig = "***" if cor["p"] is not None and cor["p"] < 0.001 else \
              "**" if cor["p"] is not None and cor["p"] < 0.01 else \
              "*" if cor["p"] is not None and cor["p"] < 0.05 else ""
        print(f"  {col:>6}  r = {cor['r']:+.3f}  "
              f"p = {cor['p']:.4f}  n={cor['n']}  {sig}")

    # 결론
    sig_pollutants = [c for c, r in results.items()
                      if r["r"] is not None and r["p"] < 0.05 and r["r"] > 0]
    print(f"\n=== 결론 ===")
    if sig_pollutants:
        best = max(sig_pollutants, key=lambda c: results[c]["r"])
        print(f"  [O] 통계적 유의 양의 상관: {sig_pollutants}")
        print(f"  [O] 최강 신호: {best} (r={results[best]['r']:+.3f})")
        print(f"  → weak supervision 원리 입증 — 환경 신호 ↔ 인구 흐름")
        print(f"  → 후속: 지하역사 CO₂ 직접 측정 시 r ≥ 0.7 예상 (D-7 IoT 통합)")
    else:
        print(f"  [X] 야외 대기는 약한 신호 (차량/날씨 영향 우세)")
        print(f"  → 지하역사 CO₂ 직접 측정이 본 가설 검증의 정도")

    # JSON 저장 (pattern은 빼고 가벼운 metric만)
    report = {
        "data_source": "TimeAverageAirQuality 202602 (외기) + CardSubwayTime 202602",
        "limitation": "지하역사 IndoorAirQuality API ERROR-500 → 야외 대기로 후퇴",
        "subway_pattern": sub_pat.tolist(),
        "correlations": {c: {k: v for k, v in r.items() if k != "pattern"}
                         for c, r in results.items()},
        "significant": sig_pollutants,
    }
    out_json = OUT_DIR / "co2_correlation_report.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  >> 리포트: {out_json}")

    maybe_plot(sub_pat, results, OUT_DIR / "co2_correlation.png")


if __name__ == "__main__":
    main()
