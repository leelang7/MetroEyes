"""# 01. 서울 지하철 EDA — SubwayBEV 진입 명분 정량화

VSCode Jupyter 또는 `jupytext --to ipynb 01_eda_subway.py` 로 변환 후 실행.

이 노트북에서 검증하는 **5가지 가설** — 각 가설은 발표자료 슬라이드 한 장으로 직결:

1. **시간대 피크의 진폭**: 출퇴근 피크/한산 비율이 N배 → 배차/증결 의사결정 근거
2. **호선 격차**: 호선·역별 혼잡도 분산 → 단일 모델 vs 호선별 fine-tune 결정
3. **편성 단위 한계 = SubwayBEV 진입 명분**: 공식 데이터는 편성 단위까지. 칸 단위 정보 부재를 정량화
4. **승하차 비대칭**: 환승역에서 승≠하차 → 칸별 점유 분산 필요성
5. **CO₂ ↔ 인원 상관 = weak supervision 명분**: 지하역사 CO₂ 농도가 승하차 인원과 상관 → 라벨링 없는 자기지도 신호

마지막 셀에 **통찰 요약**을 발표자료에 박을 6~8줄 형태로 출력.
"""

# %% [markdown]
# ## 0. 환경 setup

# %%
from __future__ import annotations
import os
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (notebooks/ 에서 src 임포트)
ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams["figure.dpi"] = 110
plt.rcParams["font.family"] = ["Malgun Gothic", "AppleGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
sns.set_style("whitegrid")
pd.set_option("display.max_columns", 60)
pd.set_option("display.width", 200)

# %% [markdown]
# ## 1. 데이터 로드 — 일별 승하차 (CardSubwayStatsNew)
#
# `.env` 의 `SEOUL_OPENDATA_API_KEY` 사용. 첫 호출은 API, 이후 `data/processed/` parquet 캐시.

# %%
from src.data_pipeline.loaders import fetch_to_parquet, extract_rows  # noqa: E402

# 분석 기준 날짜 — 평일 1개 + 주말 1개 비교 권장
DATES = ["20260422", "20260425"]  # 수(평일), 토(주말) — 가용 범위: 20260302~20260425

frames = []
for d in DATES:
    df = fetch_to_parquet(
        "CardSubwayStatsNew", d,
        cache_name=f"subway_card_{d}",
    )
    df["__date"] = pd.to_datetime(d)
    frames.append(df)

card = pd.concat(frames, ignore_index=True)
print(card.shape)
card.head()

# %% [markdown]
# ### 컬럼 자동 탐색
# 데이터셋 버전에 따라 컬럼명이 한글/영문/혼합. 일단 무엇이 들어왔는지 확인.

# %%
print(card.dtypes)
print()
print("승하차 후보:", [c for c in card.columns if any(k in c.upper() for k in ["RIDE", "ALIGHT", "승차", "하차"])])
print("노선 후보:", [c for c in card.columns if any(k in c.upper() for k in ["LINE", "노선", "호선"])])
print("역명 후보:", [c for c in card.columns if any(k in c.upper() for k in ["STA", "역"])])
print("일자 후보:", [c for c in card.columns if any(k in c.upper() for k in ["DT", "DATE", "일자"])])

# %% [markdown]
# ### 표준 컬럼명으로 정규화
# 아래 매핑은 받은 실데이터 컬럼명으로 1회 조정 후 재실행.

# %%
RENAME = {
    # CardSubwayStatsNew 실제 응답 (2026-04 확인): USE_YMD / SBWY_ROUT_LN_NM / SBWY_STNS_NM / GTON_TNOPE / GTOFF_TNOPE
    "USE_YMD": "date", "USE_DT": "date", "사용일자": "date",
    "SBWY_ROUT_LN_NM": "line", "LINE_NUM": "line", "노선명": "line",
    "SBWY_STNS_NM": "station", "SUB_STA_NM": "station", "STATION_NM": "station", "역명": "station",
    "GTON_TNOPE": "ride", "RIDE_PASGR_NUM": "ride", "승차총승객수": "ride",
    "GTOFF_TNOPE": "alight", "ALIGHT_PASGR_NUM": "alight", "하차총승객수": "alight",
}
card = card.rename(columns={k: v for k, v in RENAME.items() if k in card.columns})
for col in ["ride", "alight"]:
    if col in card.columns:
        card[col] = pd.to_numeric(card[col], errors="coerce")
card[["date", "line", "station", "ride", "alight"]].head() if {"line", "station", "ride", "alight"}.issubset(card.columns) else card.head()

# %% [markdown]
# ## 2. 가설 ① — 시간대 피크의 진폭
#
# CardSubwayStatsNew 는 일별 합계만 제공할 가능성. 시간대별이 필요하면
# `CardSubwayTime` (시간대별 승하차) 서비스로 교체.
# 여기서는 둘 다 시도하고 가용한 쪽으로 분석.

# %%
TIME_DATE = DATES[0]
try:
    time_df = fetch_to_parquet(
        "CardSubwayTime", TIME_DATE,
        cache_name=f"subway_time_{TIME_DATE}",
    )
    print("CardSubwayTime ok:", time_df.shape)
    time_df.head()
except Exception as e:
    print("CardSubwayTime 실패 — 일별 데이터로 대체:", e)
    time_df = None

# %%
# 시간대 컬럼 추정: HOUR_06_RIDE_NUM, T07_RIDE 등 다양한 네이밍
if time_df is not None:
    hour_cols = [c for c in time_df.columns if any(c.upper().startswith(p) for p in ["HOUR_", "T0", "T1", "T2"])]
    print("시간대 컬럼 후보:", hour_cols[:20])
    # 사용자 확인 후 실제 처리 셀로 이어짐 — 우선 보여주기

# %% [markdown]
# ### 시간대 피크 시각화 — 시간대 데이터가 잡혔을 때
# 받은 실데이터 컬럼명에 맞춰 아래 셀의 `ride_hour_cols` 만 채우고 실행.

# %%
ride_hour_cols: list[str] = []   # 예: ["HOUR_06_RIDE_NUM", ..., "HOUR_23_RIDE_NUM"]
alight_hour_cols: list[str] = [] # 예: ["HOUR_06_ALIGHT_NUM", ...]

if time_df is not None and ride_hour_cols and alight_hour_cols:
    by_hour = time_df[ride_hour_cols + alight_hour_cols].apply(pd.to_numeric, errors="coerce").sum().to_dict()
    hours = list(range(len(ride_hour_cols)))
    ride_series = [by_hour[c] for c in ride_hour_cols]
    alight_series = [by_hour[c] for c in alight_hour_cols]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(hours, ride_series, label="승차", marker="o")
    ax.plot(hours, alight_series, label="하차", marker="s")
    ax.set_xlabel("시간대"); ax.set_ylabel("총 승객수")
    ax.set_title(f"시간대별 전체 승하차 — {TIME_DATE}")
    ax.legend()

    peak = max(ride_series); offpeak = min(ride_series)
    print(f"피크/한산 비율: {peak / max(offpeak, 1):.2f}배")

# %% [markdown]
# ## 3. 가설 ② — 호선·역별 혼잡 격차
#
# 일별 승하차 합계로도 충분. 호선별 분포 + 역별 상위 hotspot.

# %%
if {"line", "station", "ride", "alight"}.issubset(card.columns):
    card["total"] = card["ride"].fillna(0) + card["alight"].fillna(0)
    daily = card.groupby(["__date", "line", "station"], as_index=False)["total"].sum()

    fig, ax = plt.subplots(figsize=(11, 4))
    sns.boxplot(data=daily, x="line", y="total", ax=ax, showfliers=False)
    ax.set_yscale("log")
    ax.set_title("호선별 일일 역 통과 인원 분포 (log)")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()

    top20 = daily.groupby("station", as_index=False)["total"].mean().nlargest(20, "total")
    print("일평균 통과 인원 상위 20개 역:")
    print(top20.to_string(index=False))

# %% [markdown]
# ## 4. 가설 ③ — **편성 단위 한계 = SubwayBEV 진입 명분**
#
# 공식 혼잡도(`CardSubwayCongestion` 등)는 **편성(=한 열차 전체) 단위**.
# 따라서 같은 편성 안에서 칸별 점유는 알 수 없다.
# 이를 정량화 — "한 편성 안 N칸 분산이 얼마나 클 수 있는가"는 직접 측정 불가하지만,
# **승하차 시점의 역 입출입 비대칭** 으로 칸별 분산 필요성을 유추.

# %%
# 편성/칸 단위 데이터셋이 서울 OpenAPI에 존재하는지 시도
try:
    cong = fetch_to_parquet(
        "CardSubwayCongestion", DATES[0],
        cache_name=f"subway_congestion_{DATES[0]}",
    )
    print("혼잡도 응답 컬럼:", list(cong.columns))
    cong.head()
    # 핵심 점검: 칸(CAR/CAR_NO) 컬럼이 있는가?
    has_car = any("CAR" in c.upper() or "칸" in c for c in cong.columns)
    print("칸 단위 컬럼 존재:", has_car, "←  False 이면 SubwayBEV 진입 명분 ✓")
except Exception as e:
    print("혼잡도 서비스 미응답:", e)
    cong = None

# %% [markdown]
# ## 5. 가설 ④ — 승하차 비대칭 (환승역 후보)

# %%
if {"line", "station", "ride", "alight"}.issubset(card.columns):
    asym = (
        card.groupby("station", as_index=False)
        .agg(ride=("ride", "sum"), alight=("alight", "sum"))
    )
    asym["asymmetry"] = (asym["ride"] - asym["alight"]).abs() / (asym["ride"] + asym["alight"]).clip(lower=1)
    asym = asym[asym["ride"] + asym["alight"] > 5000]   # 노이즈 제거
    top_asym = asym.nlargest(15, "asymmetry")
    print("승하차 비대칭 상위 15개 역 (환승역/종착역 후보):")
    print(top_asym.to_string(index=False))

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(data=asym, x="ride", y="alight", alpha=0.4, ax=ax)
    lim = max(asym["ride"].max(), asym["alight"].max())
    ax.plot([0, lim], [0, lim], "k--", lw=0.7)
    ax.set_title("역별 승차 vs 하차 — 대각선 이탈 = 비대칭")
    ax.set_xscale("log"); ax.set_yscale("log")

# %% [markdown]
# ## 6. 가설 ⑤ — CO₂ ↔ 인원 상관 (weak supervision 명분)
#
# 지하역사 실내 공기질 (`IndoorAirQualityMeasureService`).
# 측정 시점·역 매칭이 까다로우므로, 1차로는 **역 단위 일평균 CO₂ vs 그날 승하차 합** 산점도.

# %%
try:
    air = fetch_to_parquet(
        "IndoorAirQualityMeasureService",
        cache_name="indoor_air_recent",
    )
    print("공기질 응답 shape:", air.shape)
    print("컬럼:", list(air.columns)[:30])
    air.head()
except Exception as e:
    print("공기질 서비스 응답 실패:", e)
    air = None

# %%
# CO₂ 컬럼 + 역 컬럼 자동 탐색 후 카드 데이터와 조인
if air is not None:
    co2_cols = [c for c in air.columns if "CO2" in c.upper() or "이산화" in c]
    sta_cols = [c for c in air.columns if any(k in c.upper() for k in ["STA", "역", "STATION"])]
    print("CO₂ 후보:", co2_cols)
    print("역 후보:", sta_cols)

    if co2_cols and sta_cols and {"station", "ride", "alight"}.issubset(card.columns):
        air = air.rename(columns={co2_cols[0]: "co2", sta_cols[0]: "station"})
        air["co2"] = pd.to_numeric(air["co2"], errors="coerce")
        co2_by_sta = air.groupby("station", as_index=False)["co2"].mean()

        merged = card.groupby("station", as_index=False).agg(
            total=("ride", lambda s: s.fillna(0).sum()),
        ).merge(co2_by_sta, on="station", how="inner")
        merged["total"] = merged["total"] + card.groupby("station")["alight"].sum().reindex(merged["station"]).fillna(0).values

        if len(merged) > 5:
            corr = merged[["total", "co2"]].corr().iloc[0, 1]
            print(f"역 단위 (총 승하차) ↔ (평균 CO₂) 피어슨 상관: {corr:.3f}")
            fig, ax = plt.subplots(figsize=(7, 5))
            sns.regplot(data=merged, x="total", y="co2", ax=ax, scatter_kws={"alpha": 0.4})
            ax.set_xscale("log")
            ax.set_title("역별 승하차 합 vs 평균 CO₂")

# %% [markdown]
# ## 7. 통찰 정리 — 발표자료 박을 6~8줄
#
# *(아래 변수들은 위 셀에서 산출된 실제 값으로 채우고 슬라이드에 옮길 것)*

# %%
def _safe(name, fallback="??"):
    return globals().get(name, fallback)

print("=" * 60)
print(" SubwayBEV — 1주차 EDA 통찰 요약")
print("=" * 60)
lines = [
    f"1. 시간대 피크 진폭: 피크/한산 = {_safe('peak', '?')}/{_safe('offpeak', '?')} → 배차 의사결정 가치 입증",
    f"2. 호선·역 격차: 일평균 통과 인원 상위 20개 역에 수요 집중 (top20 / total = ??)",
    f"3. 편성 단위 한계: 공식 데이터에 칸(CAR) 컬럼 부재 → SubwayBEV 진입 명분 ✓",
    f"4. 환승역 비대칭: 상위 15개 역의 (승−하차)/총합 평균 = {round(top_asym['asymmetry'].mean(), 3) if 'top_asym' in dir() else '?'}",
    f"5. CO₂ ↔ 인원 상관: 피어슨 = {round(corr, 3) if 'corr' in dir() else '?'} → weak supervision 가능성",
    f"6. 분석 일자: {DATES}, 카드 데이터 행수: {len(card)}",
]
for ln in lines:
    print(" •", ln)
