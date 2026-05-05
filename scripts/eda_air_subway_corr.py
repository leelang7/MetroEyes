"""자치구 시간대별 미세먼지 vs 지하철 통행 상관 분석.

결합 가설:
  - 미세먼지(PM10/PM2.5) 높은 자치구 시간대 → 지하철 통행 증가 (대중교통 회피→몰림)?
  - 또는 반대 (외출 자제 → 통행 감소)?
  - 정책 ROI: 미세먼지 높은 시간대 분산 인센티브 강화 권고 가능

산출:
  outputs/air_subway_corr_report.json
  outputs/air_subway_corr_scatter.png  (PM10 vs 시간당 통행)
  outputs/air_subway_corr_heatmap.png  (자치구 × 시간대 PM10/통행 비율)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

ROOT = Path(__file__).resolve().parent.parent
SUBWAY = ROOT / "data" / "processed" / "subway_time_202602.parquet"
AIR = ROOT / "data" / "processed" / "air_202602.parquet"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def main():
    print("=" * 70)
    print("MetroEyes EDA — 미세먼지 × 지하철 통행 결합 상관 분석")
    print("=" * 70)

    if not SUBWAY.exists() or not AIR.exists():
        raise SystemExit(f"필수 데이터 없음: {SUBWAY} 또는 {AIR}")

    try:
        import pandas as pd
    except ImportError:
        raise SystemExit("pandas 미설치")

    # 미세먼지 — 자치구별 시간당 측정
    da = pd.read_parquet(AIR)
    print(f"\n[load air] {len(da):,}행 × {len(da.columns)}컬럼")
    print(f"[cols] {list(da.columns)[:10]}")

    # 지하철 — 호선별 역 시간대
    ds = pd.read_parquet(SUBWAY)
    print(f"\n[load subway] {len(ds):,}행 × 호선 {ds['SBWY_ROUT_LN_NM'].nunique()}")

    # 시간대별 통행 합계 (전 호선/전 역)
    hourly_traffic = []
    for h in range(5, 24):
        on_col = f"HR_{h}_GET_ON_NOPE"
        if on_col in ds.columns:
            hourly_traffic.append({"hour": h, "on_total": int(ds[on_col].sum())})
    df_traf = pd.DataFrame(hourly_traffic)

    # 미세먼지 시간별 평균 — air 데이터에서 hour 추출
    pm_cols = [c for c in da.columns if "PM10" in c.upper() or "PM2" in c.upper() or "MSRDT" in c.upper()]
    print(f"\n[air pm cols] {pm_cols[:6]}")

    # 컬럼명 자동 탐지
    pm10_col = None
    pm25_col = None
    time_col = None
    for c in da.columns:
        cu = c.upper()
        if pm10_col is None and "PM10" in cu and "VALUE" in cu:
            pm10_col = c
        elif pm10_col is None and cu == "PM10":
            pm10_col = c
        if pm25_col is None and ("PM25" in cu or "PM2.5" in cu) and ("VALUE" in cu or cu in ("PM25", "PM2_5")):
            pm25_col = c
        if time_col is None and ("MSRDT" in cu or "DATE" in cu or "TIME" in cu):
            time_col = c

    if pm10_col is None:
        # fallback: PM10 직접 매칭
        for c in da.columns:
            if "PM10" in c.upper():
                pm10_col = c; break

    if pm10_col is None or time_col is None:
        print(f"[warn] PM10 또는 time 컬럼 미발견 — pm10={pm10_col} time={time_col}")
        print(f"  사용 가능 컬럼: {list(da.columns)}")
        return

    print(f"\n[detected] pm10={pm10_col} pm25={pm25_col} time={time_col}")

    # 시간 추출
    da["_hour"] = pd.to_datetime(da[time_col].astype(str), errors='coerce').dt.hour
    pm_hourly = da.groupby("_hour")[pm10_col].agg(['mean', 'std', 'count']).reset_index()
    pm_hourly.columns = ["hour", "pm10_mean", "pm10_std", "n"]
    pm_hourly = pm_hourly[(pm_hourly["hour"] >= 5) & (pm_hourly["hour"] <= 23)]

    print(f"\n[pm10 hourly] {len(pm_hourly)}행")
    print(pm_hourly.round(1).to_string(index=False))

    # 결합
    merged = df_traf.merge(pm_hourly, on="hour", how="inner")
    print(f"\n[merged] {len(merged)}행")

    # 상관관계
    if len(merged) >= 5:
        corr_pearson = merged[["on_total", "pm10_mean"]].corr().iloc[0, 1]
        # Spearman (순위)
        from scipy import stats as scistats
        try:
            spearman, p_val = scistats.spearmanr(merged["on_total"], merged["pm10_mean"])
        except ImportError:
            spearman, p_val = None, None

        print(f"\n[상관관계]")
        print(f"  Pearson  (선형): r = {corr_pearson:.3f}")
        if spearman is not None:
            print(f"  Spearman (순위): ρ = {spearman:.3f} (p={p_val:.3f})")

        if abs(corr_pearson) > 0.3:
            direction = "양의" if corr_pearson > 0 else "음의"
            print(f"\n  → {direction} 상관 — 미세먼지 ↑ 시 통행 {'증가' if corr_pearson > 0 else '감소'}")
            if corr_pearson > 0.3:
                print(f"  → 정책 함의: 미세먼지 높은 시간대 분산 인센티브 강화 권고")
            else:
                print(f"  → 정책 함의: 미세먼지 높은 시간대 = 외출 자제 → 통행 분산 자연 발생")
        else:
            print(f"\n  → 약한 상관 — PM10 단독 효과는 제한적, 다변량 분석 필요")
    else:
        corr_pearson = None
        spearman = None

    # JSON 저장
    summary = {
        "n_hours": len(merged),
        "pearson_r": float(corr_pearson) if corr_pearson is not None else None,
        "spearman_rho": float(spearman) if spearman is not None else None,
        "spearman_p": float(p_val) if spearman is not None else None,
        "merged": merged.to_dict("records"),
        "interpretation": (
            "양의 상관 (PM10↑ → 통행↑) 시 정책: 미세먼지 시간대 분산 인센티브 강화"
            if corr_pearson and corr_pearson > 0.3 else
            "음의 상관 (PM10↑ → 통행↓) 시 정책: 외출 자제로 자연 분산"
            if corr_pearson and corr_pearson < -0.3 else
            "약한 상관 — PM10 단독은 ROI 정책에 큰 영향 없음 (다변량 추가 필요)"
        ),
    }
    with (OUT / "air_subway_corr_report.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n  >> {OUT / 'air_subway_corr_report.json'}")

    # PNG
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for name in ("Malgun Gothic", "NanumGothic"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break
        fig, ax = plt.subplots(figsize=(9, 5.5))
        ax.scatter(merged["pm10_mean"], merged["on_total"]/1e6, s=80,
                   c=merged["hour"], cmap="viridis", edgecolors="white", linewidth=0.5)
        for _, r in merged.iterrows():
            ax.annotate(f"{int(r['hour'])}시", (r["pm10_mean"], r["on_total"]/1e6),
                        fontsize=8, ha="center", va="bottom", color="gray")
        ax.set_xlabel("PM10 시간 평균 (μg/㎥)")
        ax.set_ylabel("지하철 통행 시간당 (M명)")
        title = f"PM10 × 지하철 통행 상관 — Pearson r={corr_pearson:.3f}" if corr_pearson else "PM10 × 통행"
        ax.set_title(title)
        plt.tight_layout()
        png = OUT / "air_subway_corr_scatter.png"
        plt.savefig(png, dpi=120); plt.close()
        print(f"  >> {png}")
    except Exception as e:
        print(f"[warn] 그림 실패: {e}")


if __name__ == "__main__":
    main()
