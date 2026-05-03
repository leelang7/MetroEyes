"""1주차 EDA 시각화 — 6장 PNG 생성.

생성 위치: outputs/figs/
실행:
    .venv/Scripts/python scripts/eda_viz.py

도시철도(서울교통공사 1~9호선 + 우이신설/신림 등) 와
코레일(경부/경인/경의/경춘/분당/수인분당 등)을 구분 — SubwayBEV 1차 타깃은 도시철도.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import seaborn as sns

from src.data_pipeline.loaders import fetch_to_parquet

WEEKDAY = "20260422"   # 수
WEEKEND = "20260425"   # 토
OUT = ROOT / "outputs" / "figs"
OUT.mkdir(parents=True, exist_ok=True)


def _setup_korean_font() -> str:
    """Windows/Mac/Linux 순으로 한글 폰트 직접 등록 후 family 이름 반환."""
    candidates = [
        r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\malgunbd.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            fm.fontManager.addfont(p)
            name = fm.FontProperties(fname=p).get_name()
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return name
    return "DejaVu Sans"


_setup_korean_font()
plt.rcParams["figure.dpi"] = 130
sns.set_style("whitegrid", {"font.family": plt.rcParams["font.family"]})

RENAME = {
    "USE_YMD": "date",
    "SBWY_ROUT_LN_NM": "line",
    "SBWY_STNS_NM": "station",
    "GTON_TNOPE": "ride",
    "GTOFF_TNOPE": "alight",
}

URBAN_HINTS = ("호선", "우이신설", "신림", "공항철도")  # 도시철도(타깃)


def is_urban(line: str) -> bool:
    return any(h in line for h in URBAN_HINTS)


def load(date: str) -> pd.DataFrame:
    df = fetch_to_parquet("CardSubwayStatsNew", date, cache_name=f"subway_card_{date}")
    df = df.rename(columns=RENAME)
    df["ride"] = pd.to_numeric(df["ride"], errors="coerce")
    df["alight"] = pd.to_numeric(df["alight"], errors="coerce")
    df["__date"] = pd.to_datetime(date)
    df["__day"] = "평일" if pd.to_datetime(date).weekday() < 5 else "주말"
    df["urban"] = df["line"].map(is_urban)
    return df


def save(fig: plt.Figure, name: str) -> None:
    path = OUT / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved → {path.relative_to(ROOT)}")


def fig1_line_bars(df: pd.DataFrame) -> None:
    by = (
        df.groupby(["line", "__day", "urban"], as_index=False)
        .agg(total=("ride", lambda s: s.fillna(0).sum() + 0))
    )
    by["total"] = by["total"] + df.groupby(["line", "__day", "urban"])["alight"].sum().fillna(0).reset_index(drop=True)
    order = (
        by.groupby("line")["total"].sum().sort_values(ascending=False).head(14).index.tolist()
    )
    by = by[by["line"].isin(order)]

    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(
        data=by, x="line", y="total", hue="__day",
        order=order, palette={"평일": "#2E86AB", "주말": "#E08E45"}, ax=ax,
    )
    # 코레일 라벨 회색 처리
    for tick, lbl in zip(ax.get_xticklabels(), order):
        if not is_urban(lbl):
            tick.set_color("#888")
    ax.set_xlabel("")
    ax.set_ylabel("일일 통과 인원 (승+하차)")
    ax.set_title(f"호선별 일일 통과 인원 — 평일({WEEKDAY}) vs 주말({WEEKEND})  ※회색=코레일")
    ax.tick_params(axis="x", rotation=35)
    ax.yaxis.set_major_formatter(lambda x, _: f"{int(x/1000):,}K")
    ax.legend(title="")
    save(fig, "01_line_bars")


def fig2_station_hotspot(df: pd.DataFrame) -> None:
    df["total"] = df["ride"].fillna(0) + df["alight"].fillna(0)
    top = (
        df.groupby(["station", "line"], as_index=False)["total"].sum()
        .sort_values("total", ascending=False)
        .drop_duplicates("station")          # 환승역은 가장 큰 노선 1개만 표기
        .head(30)
    )
    top["urban"] = top["line"].map(is_urban)

    fig, ax = plt.subplots(figsize=(8, 9))
    palette = {True: "#2E86AB", False: "#bbbbbb"}
    bars = ax.barh(
        y=top["station"][::-1], width=top["total"][::-1],
        color=[palette[u] for u in top["urban"][::-1]],
    )
    ax.set_xlabel("일일 통과 인원")
    ax.set_title("Top 30 역 — SubwayBEV 우선 배포 후보 (파랑=도시철도, 회색=코레일)")
    ax.xaxis.set_major_formatter(lambda x, _: f"{int(x/1000):,}K")
    save(fig, "02_station_top30")


def fig3_weekday_vs_weekend(df: pd.DataFrame) -> None:
    pivot = (
        df.assign(total=df["ride"].fillna(0) + df["alight"].fillna(0))
        .groupby(["station", "__day"])["total"].sum().unstack().dropna()
    )
    pivot["urban"] = pivot.index.map(
        lambda s: any(is_urban(ln) for ln in df[df["station"] == s]["line"].unique())
    )

    fig, ax = plt.subplots(figsize=(7, 7))
    for u, color in [(True, "#2E86AB"), (False, "#bbbbbb")]:
        sub = pivot[pivot["urban"] == u]
        ax.scatter(sub["평일"], sub["주말"], alpha=0.55, s=14, c=color,
                   label="도시철도" if u else "코레일")
    lim = max(pivot["평일"].max(), pivot["주말"].max()) * 1.05
    ax.plot([0, lim], [0, lim], "k--", lw=0.7, label="평일=주말")
    # 극단치 라벨
    pivot["ratio"] = pivot["평일"] / pivot["주말"].clip(lower=1)
    extreme = pd.concat([
        pivot.nlargest(6, "ratio"),
        pivot.nsmallest(6, "ratio")[pivot.nsmallest(6, "ratio")["주말"] > 5000],
    ])
    for sta, row in extreme.iterrows():
        ax.annotate(sta, (row["평일"], row["주말"]), fontsize=8, alpha=0.8)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("평일 통과 인원 (log)")
    ax.set_ylabel("주말 통과 인원 (log)")
    ax.set_title("역별 평일 vs 주말 — 대각선 이탈 = 평일 편향")
    ax.legend()
    save(fig, "03_weekday_vs_weekend")


def fig4_ride_vs_alight(df: pd.DataFrame) -> None:
    sta = (
        df.groupby("station", as_index=False)
        .agg(ride=("ride", "sum"), alight=("alight", "sum"))
    )
    sta = sta[sta["ride"] + sta["alight"] > 5000]
    sta["urban"] = sta["station"].map(
        lambda s: any(is_urban(ln) for ln in df[df["station"] == s]["line"].unique())
    )
    fig, ax = plt.subplots(figsize=(7, 7))
    for u, color in [(True, "#2E86AB"), (False, "#bbbbbb")]:
        sub = sta[sta["urban"] == u]
        ax.scatter(sub["ride"], sub["alight"], alpha=0.55, s=14, c=color,
                   label="도시철도" if u else "코레일")
    lim = max(sta["ride"].max(), sta["alight"].max()) * 1.05
    ax.plot([0, lim], [0, lim], "k--", lw=0.7)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("승차 합 (log)")
    ax.set_ylabel("하차 합 (log)")
    ax.set_title("역별 승차 vs 하차 — 대각선 이탈 = 비대칭")
    ax.legend()
    save(fig, "04_ride_vs_alight")


def fig5_golden(df: pd.DataFrame) -> None:
    """🌟 골든 — 통행 많을수록 비대칭은 0에 수렴.

    'SubwayBEV 핵심 메시지: 총량은 균형이지만 그 안의 칸별 점유는 알 수 없다.'
    """
    sta = (
        df.groupby("station", as_index=False)
        .agg(ride=("ride", "sum"), alight=("alight", "sum"))
    )
    sta["total"] = sta["ride"] + sta["alight"]
    sta = sta[sta["total"] > 5000].copy()
    sta["asym"] = (sta["ride"] - sta["alight"]).abs() / sta["total"]
    sta["urban"] = sta["station"].map(
        lambda s: any(is_urban(ln) for ln in df[df["station"] == s]["line"].unique())
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    for u, color in [(True, "#2E86AB"), (False, "#bbbbbb")]:
        sub = sta[sta["urban"] == u]
        ax.scatter(sub["total"], sub["asym"], alpha=0.55, s=14, c=color,
                   label="도시철도" if u else "코레일")

    # 회귀선 (도시철도만)
    urban = sta[sta["urban"]].copy()
    urban["log_total"] = np.log10(urban["total"])
    coef = np.polyfit(urban["log_total"], urban["asym"], 1)
    xs = np.logspace(np.log10(urban["total"].min()), np.log10(urban["total"].max()), 80)
    ax.plot(xs, coef[0] * np.log10(xs) + coef[1], "r-", lw=1.5, alpha=0.7,
            label=f"도시철도 추세선 (slope={coef[0]:.3f})")

    # 핵심 환승역 라벨
    transfers = ["고속터미널", "사당", "강남", "서울역", "잠실(송파구청)", "홍대입구",
                 "왕십리", "건대입구", "신도림", "교대", "동대문역사문화공원"]
    for name in transfers:
        row = sta[sta["station"] == name]
        if len(row):
            r = row.iloc[0]
            ax.annotate(name, (r["total"], r["asym"]), fontsize=8.5,
                        ha="left", va="bottom", color="#1A4F7A")

    ax.set_xscale("log")
    ax.set_xlabel("일일 총 통과 인원 (log)")
    ax.set_ylabel("승하차 비대칭 |승-하차| / 총합")
    ax.set_title("[★] 통행 많을수록 비대칭은 0에 수렴 — '총량은 균형, 칸별은 미지'")
    ax.legend(loc="upper right")
    ax.set_ylim(-0.02, sta["asym"].quantile(0.98) * 1.05)
    save(fig, "05_golden_asymmetry_vs_traffic")


def fig6_line_boxplot(df: pd.DataFrame) -> None:
    df["total"] = df["ride"].fillna(0) + df["alight"].fillna(0)
    daily = df.groupby(["line", "station"], as_index=False)["total"].mean()
    daily = daily[daily["line"].map(is_urban)]
    order = daily.groupby("line")["total"].median().sort_values(ascending=False).index.tolist()

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=daily, x="line", y="total", order=order, ax=ax, color="#2E86AB", showfliers=True)
    ax.set_yscale("log")
    ax.set_xlabel("")
    ax.set_ylabel("역 단위 일평균 통과 인원 (log)")
    ax.set_title("도시철도 호선별 역 분포 — 호선 내 격차")
    ax.tick_params(axis="x", rotation=30)
    save(fig, "06_line_distribution")


def main() -> None:
    print("[load]")
    df = pd.concat([load(WEEKDAY), load(WEEKEND)], ignore_index=True)
    print(f"  rows={len(df)} stations={df['station'].nunique()} lines={df['line'].nunique()}")

    print("[render]")
    fig1_line_bars(df)
    fig2_station_hotspot(df)
    fig3_weekday_vs_weekend(df)
    fig4_ride_vs_alight(df)
    fig5_golden(df)
    fig6_line_boxplot(df)
    print("[done]")


if __name__ == "__main__":
    main()
