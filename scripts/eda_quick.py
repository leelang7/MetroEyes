"""1주차 EDA — 콘솔 통찰만 빠르게 뽑는 스크립트.

CardSubwayStatsNew (일별 승하차)로 검증 가능한 가설:
  ①'  평일 vs 주말 진폭                 (시간대별 데이터는 별도 서비스 필요 → 후속)
  ②   호선·역별 혼잡 격차
  ③   편성 단위 한계 = SubwayBEV 진입 명분 (스키마 부재로 입증)
  ④   승하차 비대칭 (환승역 후보)
  ⑤   CO₂ ↔ 인원 상관             (IndoorAir API 인자 보강 후 → 후속)

실행:
    .venv/Scripts/python scripts/eda_quick.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.data_pipeline.loaders import fetch_to_parquet

WEEKDAY = "20260422"   # 수요일
WEEKEND = "20260425"   # 토요일

RENAME = {
    "USE_YMD": "date",
    "SBWY_ROUT_LN_NM": "line",
    "SBWY_STNS_NM": "station",
    "GTON_TNOPE": "ride",
    "GTOFF_TNOPE": "alight",
}


def load_day(date: str) -> pd.DataFrame:
    df = fetch_to_parquet("CardSubwayStatsNew", date, cache_name=f"subway_card_{date}")
    df = df.rename(columns=RENAME)
    df["ride"] = pd.to_numeric(df["ride"], errors="coerce")
    df["alight"] = pd.to_numeric(df["alight"], errors="coerce")
    df["__date"] = pd.to_datetime(date)
    return df


def banner(s: str) -> None:
    print()
    print("=" * 64)
    print(s)
    print("=" * 64)


def main() -> None:
    banner("0. 데이터 로드")
    wd = load_day(WEEKDAY)
    we = load_day(WEEKEND)
    print(f"  평일 {WEEKDAY} rows={len(wd):>5}  cols={list(wd.columns)}")
    print(f"  주말 {WEEKEND} rows={len(we):>5}")
    print(f"  스키마 점검 — 칸(CAR/CAR_NO) 컬럼 존재? {any('CAR' in c.upper() or '칸' in c for c in wd.columns)}  ← False = 가설 ③ ✓")

    df = pd.concat([wd, we], ignore_index=True)
    df["total"] = df["ride"].fillna(0) + df["alight"].fillna(0)

    # ---- 가설 ①' 평일/주말 진폭 ----
    banner("① 평일 vs 주말 진폭")
    by_day = df.groupby("__date")["total"].sum()
    print(by_day.to_string())
    ratio = by_day.iloc[0] / max(by_day.iloc[1], 1)
    print(f"  평일/주말 총량 비율: {ratio:.2f}배")
    # 비율이 클수록 평일 운영 최적화 가치 ↑

    # ---- 가설 ② 호선 격차 ----
    banner("② 호선·역 격차")
    by_line = df.groupby("line")["total"].sum().sort_values(ascending=False)
    total_all = by_line.sum()
    print("호선별 일평균 통과 인원 (Top 10):")
    print(by_line.head(10).to_string())
    print(f"  Top1 호선 점유율: {by_line.iloc[0] / total_all:.1%}")
    print(f"  호선 분산(CV) = std/mean = {by_line.std() / by_line.mean():.2f}")

    # 역 hotspot Top 20
    by_sta = df.groupby("station", as_index=False)["total"].sum().sort_values("total", ascending=False)
    top20 = by_sta.head(20)
    top20_share = top20["total"].sum() / total_all
    print(f"\n  Top 20 역의 전체 점유율: {top20_share:.1%}  ← 이 역들에 우선 배포할 가치")
    print(top20.to_string(index=False))

    # ---- 가설 ④ 승하차 비대칭 ----
    banner("④ 승하차 비대칭 (환승역/종착역 후보)")
    asym = (
        df.groupby("station", as_index=False)
        .agg(ride=("ride", "sum"), alight=("alight", "sum"))
    )
    asym = asym[asym["ride"] + asym["alight"] > 5000]
    asym["asymmetry"] = (asym["ride"] - asym["alight"]).abs() / (asym["ride"] + asym["alight"]).clip(lower=1)
    top_asym = asym.nlargest(15, "asymmetry")
    print("비대칭 상위 15개 역:")
    print(top_asym.to_string(index=False))
    mean_asym = top_asym["asymmetry"].mean()

    # ---- 통찰 요약 ----
    banner("📌 1주차 통찰 — 발표자료 박을 6~8줄")
    print(f" • 데이터: 서울 OpenAPI CardSubwayStatsNew, 평일 {WEEKDAY} + 주말 {WEEKEND}, 총 {len(df):,} 행")
    print(f" • 평일/주말 진폭 = {ratio:.2f}배 → 평일 피크 운영 최적화 가치 명확")
    print(f" • 호선 분포 Top1 점유율 {by_line.iloc[0] / total_all:.1%}, 호선 CV={by_line.std() / by_line.mean():.2f} → 호선 fine-tune 가치 있음")
    print(f" • Top 20 역이 전체 통행의 {top20_share:.1%} → SubwayBEV 우선 배포 후보")
    print(f" • 환승역 비대칭 평균(상위 15) = {mean_asym:.2%} → 칸별 분산 필요성 입증")
    print(f" • 공식 데이터 스키마: {list(df.columns)} — 칸 단위 컬럼 ✗ → SubwayBEV 진입 명분 ✓")
    print(" • [후속] CardSubwayTime / IndoorAirQualityMeasureService 인자·서비스ID 정정 후 시간대×CO₂ 분석")


if __name__ == "__main__":
    main()
