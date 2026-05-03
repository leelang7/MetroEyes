"""시간대별 EDA 시각화 — CardSubwayTime (월별 시간대 승하차).

출력: outputs/figs/07~09_*.png
실행: .venv/Scripts/python scripts/eda_viz_hourly.py
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
import seaborn as sns

from src.data_pipeline.loaders import fetch_to_parquet

MONTH = "202602"   # 가용 월 — INFO-200 안 뜨는 가장 최근
OUT = ROOT / "outputs" / "figs"
OUT.mkdir(parents=True, exist_ok=True)


def _setup_korean_font() -> None:
    for p in (r"C:\Windows\Fonts\malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc"):
        if Path(p).exists():
            fm.fontManager.addfont(p)
            plt.rcParams["font.family"] = fm.FontProperties(fname=p).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 130


_setup_korean_font()
sns.set_style("whitegrid", {"font.family": plt.rcParams["font.family"]})

URBAN = ("호선", "우이신설", "신림", "공항철도")


def is_urban(line: str) -> bool:
    return any(h in line for h in URBAN)


def save(fig: plt.Figure, name: str) -> None:
    p = OUT / f"{name}.png"
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved → {p.relative_to(ROOT)}")


def to_long(df: pd.DataFrame) -> pd.DataFrame:
    """wide(HR_h_GET_ON/OFF_NOPE) → long(hour, action, n)."""
    rename = {"SBWY_ROUT_LN_NM": "line", "STTN": "station"}
    df = df.rename(columns=rename)
    on_cols = [c for c in df.columns if c.endswith("_GET_ON_NOPE")]
    off_cols = [c for c in df.columns if c.endswith("_GET_OFF_NOPE")]
    long_on = df.melt(id_vars=["line", "station"], value_vars=on_cols,
                      var_name="hcol", value_name="n")
    long_on["action"] = "ride"
    long_off = df.melt(id_vars=["line", "station"], value_vars=off_cols,
                       var_name="hcol", value_name="n")
    long_off["action"] = "alight"
    long = pd.concat([long_on, long_off], ignore_index=True)
    long["hour"] = long["hcol"].str.extract(r"HR_(\d+)_").astype(int)
    long["n"] = pd.to_numeric(long["n"], errors="coerce").fillna(0)
    return long.drop(columns=["hcol"])


def fig7_overall_peak(long: pd.DataFrame) -> tuple[float, float]:
    """도시철도 전체 시간대별 승하차 — 출근/퇴근 양봉."""
    urban = long[long["line"].map(is_urban)]
    by_hour = urban.groupby(["hour", "action"], as_index=False)["n"].sum()
    fig, ax = plt.subplots(figsize=(10, 5))
    pivot = by_hour.pivot(index="hour", columns="action", values="n").reindex(range(24)).fillna(0)
    ax.plot(pivot.index, pivot["ride"], "-o", color="#2E86AB", lw=2, ms=5, label="승차")
    ax.plot(pivot.index, pivot["alight"], "-s", color="#E08E45", lw=2, ms=5, label="하차")

    ride_only = urban[urban["action"] == "ride"].groupby("hour")["n"].sum()
    peak = ride_only.max()
    offpeak = ride_only[(ride_only.index >= 13) & (ride_only.index <= 15)].mean()
    night = ride_only[(ride_only.index >= 1) & (ride_only.index <= 4)].mean()
    ratio = peak / offpeak
    night_ratio = peak / max(night, 1)
    morning_peak = int(ride_only.idxmax()) if ride_only.idxmax() < 12 else 8
    evening_peak = int(ride_only[ride_only.index >= 12].idxmax())
    for h, label in [(morning_peak, "아침 피크"), (evening_peak, "저녁 피크")]:
        ax.axvline(h, color="#888", lw=0.6, ls="--", alpha=0.6)
        ax.text(h, ax.get_ylim()[1] * 0.95 if False else pivot.values.max() * 1.02,
                f"{label}\n{h}시", ha="center", va="bottom", fontsize=9, color="#444")

    ax.set_xticks(range(0, 24))
    ax.yaxis.set_major_formatter(lambda x, _: f"{int(x/1_000_000)}M")
    ax.set_xlabel("시각 (시)")
    ax.set_ylabel("월간 승하차 인원")
    ax.set_title(f"도시철도 시간대별 승하차 ({MONTH})  —  피크/한산(13~15시) = {ratio:.1f}배,  피크/심야 = {night_ratio:.0f}배")
    ax.legend(loc="upper left")
    ax.set_ylim(top=pivot.values.max() * 1.12)
    save(fig, "07_hourly_peak")
    return ratio, night_ratio


def fig8_archetypes(long: pd.DataFrame) -> None:
    """오피스 vs 주거 역 — 한 역의 승차/하차 시간대 패턴.

    각 패널에 대표 역 1개를 골라 승차/하차를 같이 그려 패턴을 명확히 보여준다.
    오피스: 아침 하차 ↑ 저녁 승차 ↑   /   주거: 아침 승차 ↑ 저녁 하차 ↑   /   환승: 양봉이 둘 다 균형
    """
    archetypes = [
        ("오피스 — 강남",     "강남",         "#1f77b4"),
        ("오피스 — 역삼",     "역삼",         "#2ca02c"),
        ("주거 — 신림",        "신림",         "#d62728"),
        ("주거 — 가산디지털단지", "가산디지털단지", "#ff7f0e"),
        ("환승 허브 — 서울역",  "서울역",       "#9467bd"),
        ("환승 허브 — 잠실",    "잠실(송파구청)", "#8c564b"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
    urban_sta = set(long[long["line"].map(is_urban)]["station"].unique())

    for ax, (title, sta, _color) in zip(axes.ravel(), archetypes):
        sub = long[(long["station"] == sta) & long["line"].map(is_urban)]
        if len(sub) == 0:
            ax.set_title(f"{title} (데이터 없음)")
            continue
        ride = sub[sub["action"] == "ride"].groupby("hour")["n"].sum().reindex(range(24)).fillna(0)
        alight = sub[sub["action"] == "alight"].groupby("hour")["n"].sum().reindex(range(24)).fillna(0)
        ax.plot(ride.index, ride.values, "-o", color="#2E86AB", lw=1.8, ms=4, label="승차")
        ax.plot(alight.index, alight.values, "-s", color="#E08E45", lw=1.8, ms=4, label="하차")
        # 어떤 시간대가 우세한지 음영으로 강조
        diff = alight - ride
        ax.fill_between(ride.index, ride.values, alight.values,
                        where=(diff > 0), color="#E08E45", alpha=0.12, label="하차 우세")
        ax.fill_between(ride.index, ride.values, alight.values,
                        where=(diff < 0), color="#2E86AB", alpha=0.12, label="승차 우세")
        ax.set_title(title, fontsize=11)
        ax.set_xticks([0, 6, 9, 12, 15, 18, 21])
        ax.yaxis.set_major_formatter(lambda x, _: f"{int(x/1000):,}K")
        ax.grid(alpha=0.3)
    for ax in axes[-1, :]:
        ax.set_xlabel("시각")
    for ax in axes[:, 0]:
        ax.set_ylabel("월간 인원")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    # 중복 제거 후 한 번만
    by_label = dict(zip(labels, handles))
    fig.legend(by_label.values(), by_label.keys(),
               loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.02), frameon=False)
    fig.suptitle(f"역 아키타입별 시간대 승하차 ({MONTH})  —  오피스: 아침 하차↑/저녁 승차↑   주거: 정반대   환승: 양쪽 균형",
                 y=1.06, fontsize=12)
    fig.tight_layout()
    save(fig, "08_station_archetypes")


def fig9_line_heatmap(long: pd.DataFrame) -> None:
    """호선 × 시간대 heatmap — 호선별 피크 시점 차이."""
    urban = long[long["line"].map(is_urban) & (long["action"] == "ride")]
    # 도시철도 1~9호선 + 우이신설/신림만
    keep = [f"{i}호선" for i in range(1, 10)] + ["우이신설선", "신림선"]
    urban = urban[urban["line"].isin(keep)]
    pivot = urban.pivot_table(index="line", columns="hour", values="n", aggfunc="sum").reindex(keep)
    # 행 정규화 — 호선 내 시간대 분포 (피크 시점이 어디인지 비교 가능)
    norm = pivot.div(pivot.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.heatmap(norm, cmap="rocket_r", ax=ax, cbar_kws={"label": "행 정규화 비율"},
                xticklabels=range(24))
    ax.set_xlabel("시각")
    ax.set_ylabel("")
    ax.set_title(f"호선 × 시간대 승차 분포 (행 정규화) — 호선마다 피크 시점·강도 다름  ({MONTH})")
    save(fig, "09_line_hour_heatmap")


def main() -> None:
    print("[fetch]")
    df = fetch_to_parquet("CardSubwayTime", MONTH, cache_name=f"subway_time_{MONTH}", page=1000, max_rows=2000)
    print(f"  rows={len(df)}  cols={len(df.columns)}")

    print("[melt]")
    long = to_long(df)
    print(f"  long rows={len(long):,}")

    print("[render]")
    ratio, night_ratio = fig7_overall_peak(long)
    fig8_archetypes(long)
    fig9_line_heatmap(long)
    print(f"\n[insight] 도시철도 시간대 진폭: 피크/낮시간 = {ratio:.2f}배, 피크/심야 = {night_ratio:.0f}배")
    print("[done]")


if __name__ == "__main__":
    main()
