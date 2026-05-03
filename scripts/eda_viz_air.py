"""대기질 × 지하철 시간대 동조 패턴.

데이터셋:
  - TimeAverageAirQuality (서울 25개 자치구 시간당 야외 대기질, 202602)
    컬럼: MSRMT_DT(YYYYMMDDHHmm), MSRSTN_NM(자치구), NTDX(NO2), OZON(O3),
          CBMX(CO), SPDX(SO2), PM(PM10), FPM(PM2.5)
  - CardSubwayTime (월별 시간대 승하차)

산출물: outputs/figs/12_hourly_air_vs_subway.png

가설 ⑤(재정의): 서울 야외 대기의 시간대 패턴이 지하철 출퇴근 양봉과 동조하는가?
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data_pipeline.loaders import fetch_to_parquet

MONTH = "202602"
OUT = ROOT / "outputs" / "figs"
OUT.mkdir(parents=True, exist_ok=True)


def _setup_font() -> None:
    for p in (r"C:\Windows\Fonts\malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc"):
        if Path(p).exists():
            fm.fontManager.addfont(p)
            plt.rcParams["font.family"] = fm.FontProperties(fname=p).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 130


_setup_font()

URBAN = ("호선", "우이신설", "신림", "공항철도")


def hourly_subway_ride() -> pd.Series:
    """도시철도 시간대별 승차 총합 (24개)."""
    df = fetch_to_parquet("CardSubwayTime", MONTH, cache_name=f"subway_time_{MONTH}",
                          page=1000, max_rows=2000)
    df = df.rename(columns={"SBWY_ROUT_LN_NM": "line"})
    df = df[df["line"].apply(lambda s: any(h in s for h in URBAN))]
    out = {}
    for h in range(24):
        col = f"HR_{h}_GET_ON_NOPE"
        if col in df.columns:
            out[h] = pd.to_numeric(df[col], errors="coerce").fillna(0).sum()
    return pd.Series(out).sort_index()


def hourly_air() -> pd.DataFrame:
    """자치구 평균 시간대별 대기질 (24 × N개 항목)."""
    df = fetch_to_parquet("TimeAverageAirQuality", MONTH, cache_name=f"air_{MONTH}",
                          page=1000, max_rows=20000)
    df["MSRMT_DT"] = df["MSRMT_DT"].astype(str)
    df["hour"] = df["MSRMT_DT"].str[8:10].astype(int)
    for c in ["NTDX", "OZON", "CBMX", "SPDX", "PM", "FPM"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.groupby("hour")[["NTDX", "OZON", "CBMX", "SPDX", "PM", "FPM"]].mean()


def fig12(ride: pd.Series, air: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 좌: 시간대 동조 (지하철 승차 vs PM2.5/NO2)
    ax = axes[0]
    ax2 = ax.twinx()
    l1, = ax.plot(ride.index, ride.values, "-o", color="#2E86AB", lw=2.2, ms=5, label="지하철 승차")
    l2, = ax2.plot(air.index, air["FPM"], "-s", color="#C44536", lw=1.8, ms=4, label="PM2.5 (FPM)")
    l3, = ax2.plot(air.index, air["NTDX"] * 1000, "-^", color="#7E4F8B", lw=1.5, ms=4, alpha=0.75,
                   label="NO2 ×1000")
    ax.set_xticks(range(0, 24, 2))
    ax.yaxis.set_major_formatter(lambda x, _: f"{int(x/1_000_000)}M")
    ax.set_xlabel("시각")
    ax.set_ylabel("월간 지하철 승차 (M명)", color="#2E86AB")
    ax2.set_ylabel("PM2.5 (㎍/㎥) · NO2×1000 (ppm)", color="#C44536")
    ax.tick_params(axis="y", labelcolor="#2E86AB")
    ax2.tick_params(axis="y", labelcolor="#C44536")
    ax.set_title("시간대 동조 — 지하철 승차 양봉 vs 야외 대기")
    ax.legend(handles=[l1, l2, l3], loc="upper left", fontsize=9)

    # 우: 상관 — 24개 시간 × (지하철, NO2, PM2.5, CO, O3)
    corr_target = pd.DataFrame({
        "지하철 승차": ride.reindex(range(24)).fillna(0).values,
        "NO2": air["NTDX"].reindex(range(24)).fillna(0).values,
        "PM2.5": air["FPM"].reindex(range(24)).fillna(0).values,
        "CO": air["CBMX"].reindex(range(24)).fillna(0).values,
        "O3": air["OZON"].reindex(range(24)).fillna(0).values,
        "PM10": air["PM"].reindex(range(24)).fillna(0).values,
    }).corr()["지하철 승차"].drop("지하철 승차").sort_values()
    colors = ["#C44536" if v > 0 else "#3A7CA5" for v in corr_target.values]
    axes[1].barh(corr_target.index, corr_target.values, color=colors, alpha=0.85)
    for y, v in enumerate(corr_target.values):
        axes[1].text(v + (0.02 if v >= 0 else -0.02), y, f"{v:+.2f}",
                     va="center", ha="left" if v >= 0 else "right", fontsize=10)
    axes[1].axvline(0, color="#888", lw=0.6)
    axes[1].set_xlim(-1.05, 1.05)
    axes[1].set_xlabel("시간대 패턴 피어슨 상관 (지하철 승차 기준)")
    axes[1].set_title("어떤 대기 항목이 지하철 패턴과 동조하는가")

    fig.suptitle(f"가설 ⑤(재정의) — 야외 대기 × 지하철 동조 분석 ({MONTH})", y=1.02, fontsize=12)
    fig.tight_layout()
    p = OUT / "12_hourly_air_vs_subway.png"
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved → {p.relative_to(ROOT)}")
    print("\n[insight] 시간대 패턴 상관 (지하철 승차 vs):")
    for k, v in corr_target.items():
        print(f"    {k:>6}: {v:+.3f}")


def main() -> None:
    print("[fetch]")
    ride = hourly_subway_ride()
    air = hourly_air()
    print(f"  ride hours={len(ride)}  air hours={len(air)}")
    print("\n  자치구 평균 대기질 24h 헤드:")
    print(air.round(3).head())

    print("\n[render]")
    fig12(ride, air)


if __name__ == "__main__":
    main()
