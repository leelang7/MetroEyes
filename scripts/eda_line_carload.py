"""호선별 칸 점유 추정 EDA.

주의: 공식 스키마에 칸(CAR) 컬럼 부재 — 1주차 EDA 골든 인사이트.
대신 호선별 시간대 통행 ÷ 차량 수 / 정원 비율로 *추정 칸 점유율* 계산.
이 데이터는 공공 OpenAPI 만으로 도출 가능한 한계 → MetroEyes CV 가
실측 칸 점유로 대체할 명분.

산출:
  outputs/line_carload_est.csv
  outputs/line_carload_heatmap.png
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed" / "subway_time_202602.parquet"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


# 호선별 차량 수 (현실 운행 기준)
LINE_CARS = {
    "1호선": 10, "2호선": 10, "3호선": 10, "4호선": 10,
    "5호선": 8, "6호선": 8, "7호선": 8, "8호선": 6, "9호선": 6,
    "수인분당선": 6, "경의중앙선": 8, "공항철도": 8,
    "신분당선": 6, "분당선": 6, "경춘선": 8,
    "우이신설선": 2, "신림선": 3,
}
# 호선별 차량당 정원 (m^2 환산)
LINE_CAPACITY = {
    "1호선": 160, "2호선": 160, "3호선": 160, "4호선": 160,
    "5호선": 140, "6호선": 140, "7호선": 140, "8호선": 130, "9호선": 130,
    "수인분당선": 130, "경의중앙선": 140, "공항철도": 140,
    "신분당선": 120, "분당선": 130, "경춘선": 140,
    "우이신설선": 100, "신림선": 100,
}
# 평균 차편 간격 (분) — 시간당 운행 횟수 환산
LINE_HEADWAY_MIN = {
    "1호선": 4.0, "2호선": 3.0, "3호선": 4.5, "4호선": 4.0,
    "5호선": 5.0, "6호선": 6.0, "7호선": 5.5, "8호선": 7.0, "9호선": 6.0,
}


def load_data() -> pd.DataFrame:
    if not DATA.exists():
        raise SystemExit(f"필수 데이터 없음: {DATA}")
    df = pd.read_parquet(DATA)
    return df


def estimate_carload(df: pd.DataFrame) -> pd.DataFrame:
    """호선 × 시간대 평균 칸 점유율 추정.

    수식 (보정):
        시간당 한 방향 승차 = HR_h_GET_ON_NOPE 합 (역수)
        OFF 는 같은 사람이 다른 역에서 내림 → ON 만 사용 (중복 회피)
        역 평균 차내 인원 = 승차합 / (역수 × (60/headway) × 양방향 2)
        차량당 = 그 인원 / cars
        점유율 = 차량당 / capacity
    """
    rows = []
    for h in range(5, 24):
        on_col = f"HR_{h}_GET_ON_NOPE"
        off_col = f"HR_{h}_GET_OFF_NOPE"
        if on_col not in df.columns or off_col not in df.columns:
            continue
        for line, sub in df.groupby("SBWY_ROUT_LN_NM"):
            on_total = float(sub[on_col].sum())
            off_total = float(sub[off_col].sum())
            cars = LINE_CARS.get(line, 8)
            cap = LINE_CAPACITY.get(line, 140)
            headway = LINE_HEADWAY_MIN.get(line, 5.0)
            n_stations = max(1, sub["STTN"].nunique())
            trains_per_h = 60.0 / headway
            # ON 만 사용 + 양방향 분리 (상행/하행)
            # 시간당 노선 전체에서 차편 1 대당 받는 평균 승차 = on_total / (trains_per_h * 2)
            per_train_ride = on_total / (trains_per_h * 2)
            # 차편 안에서 머무는 평균 인원: 승차 후 평균 5정거장 머무름 가정 (n_stations / 6 정도)
            avg_dwell_stations = max(2, n_stations / 8)  # 짧은 노선은 더 짧게
            per_train_avg = per_train_ride * avg_dwell_stations / max(1, n_stations / trains_per_h)
            per_car = per_train_avg / cars
            occ = min(2.0, per_car / cap)  # cap 200% (만석 + 입석)
            rows.append({
                "line": line, "hour": h,
                "on_total": int(on_total), "off_total": int(off_total),
                "n_stations": n_stations, "trains_per_h": round(trains_per_h, 1),
                "per_car_avg": round(per_car, 1),
                "occ_pct": round(occ * 100, 1),
            })
    return pd.DataFrame(rows)


def main():
    df = load_data()
    print(f"[load] {len(df)}행 × {len(df.columns)}컬럼 — {df['SBWY_ROUT_LN_NM'].nunique()}개 호선")
    est = estimate_carload(df)
    print(f"\n[estimate] {len(est)}행 (호선 × 시간대)")

    # Pivot: 호선 × 시간대 점유율 매트릭스
    pivot = est.pivot(index="line", columns="hour", values="occ_pct").fillna(0)
    # 1호선~9호선 + 일부만
    main_lines = [f"{i}호선" for i in range(1, 10) if f"{i}호선" in pivot.index]
    pivot = pivot.loc[main_lines]
    print("\n[pivot] 호선 × 시간대 점유율 (%) — 핵심 호선만:")
    with pd.option_context("display.max_columns", 20, "display.width", 200):
        print(pivot.round(0).astype(int).to_string())

    # 발견 사항
    print("\n[insight]")
    peak_h_per_line = pivot.idxmax(axis=1)
    peak_v_per_line = pivot.max(axis=1)
    print("  호선별 최대 점유 시간대:")
    for line in pivot.index:
        print(f"    {line}: {peak_h_per_line[line]}시 ({peak_v_per_line[line]:.0f}%)")

    avg_pct = pivot.mean().mean()
    max_pct = pivot.max().max()
    print(f"\n  전체 평균 점유율 추정: {avg_pct:.1f}%")
    print(f"  최대 점유율 추정     : {max_pct:.1f}%")
    print(f"  → 100% 이상 = 칸 단위 분산 필요 (현재 평균값 단위 운영 → 일부 칸 입석)")

    # CSV 저장
    csv_out = OUT / "line_carload_est.csv"
    est.to_csv(csv_out, index=False, encoding="utf-8-sig")
    print(f"\n  >> {csv_out}")

    # heatmap
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for name in ("Malgun Gothic", "NanumGothic"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break
        fig, ax = plt.subplots(figsize=(13, 5))
        im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        ax.set_xlabel("시간 (시)")
        ax.set_ylabel("호선")
        ax.set_title("호선별 시간대 추정 칸 점유율 (%) — CardSubwayTime 202602")
        plt.colorbar(im, ax=ax, label="점유율 %")
        # 셀에 수치 표기
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                v = pivot.iloc[i, j]
                if v > 5:
                    ax.text(j, i, f"{int(v)}", ha="center", va="center",
                            fontsize=7, color="black" if v < 50 else "white")
        plt.tight_layout()
        png = OUT / "line_carload_heatmap.png"
        plt.savefig(png, dpi=120)
        print(f"  >> {png}")
    except ImportError:
        pass

    # JSON 산출
    summary = {
        "lines": len(main_lines),
        "avg_occ_pct": float(avg_pct),
        "max_occ_pct": float(max_pct),
        "peak_hours": {line: int(peak_h_per_line[line]) for line in pivot.index},
        "peak_values": {line: float(peak_v_per_line[line]) for line in pivot.index},
        "limitation": "공식 CardSubwayTime 은 칸 컬럼 부재 — 호선 평균 추정값. 실 칸별 점유는 MetroEyes CV 필요.",
    }
    with (OUT / "line_carload_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
