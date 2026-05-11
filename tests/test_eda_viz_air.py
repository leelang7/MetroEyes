"""eda_viz_air.py 회귀 가드 (cycle 536).

대기질(TimeAverageAirQuality) × 지하철 시간대 동조 시각화.
공공데이터: 서울 25개 자치구 시간당 야외 대기질 + CardSubwayTime.
피치 근거: 가설 ⑤ 야외 PM10 × 통근 양봉 동조 패턴 정량.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "eda_viz_air.py"


def test_script_exists() -> None:
    assert SCRIPT.exists(), f"스크립트 없음: {SCRIPT}"


def test_uses_timeaveragairquality_dataset() -> None:
    """TimeAverageAirQuality 서울 열린데이터광장 데이터셋 사용."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "TimeAverageAirQuality" in src, "TimeAverageAirQuality 데이터셋 미사용"


def test_uses_cardsubwaytime_dataset() -> None:
    """CardSubwayTime 지하철 시간대 데이터 결합."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "CardSubwayTime" in src, "CardSubwayTime 결합 없음"


def test_month_constant_202602() -> None:
    """2026년 2월 데이터 (MONTH = '202602')."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert '"202602"' in src or "'202602'" in src, "MONTH 202602 없음"


def test_air_pollutants_covered() -> None:
    """주요 대기오염물질 (PM, NO2, O3, CO, SO2) 모두 포함."""
    src = SCRIPT.read_text(encoding="utf-8")
    for p in ("NTDX", "OZON", "CBMX", "SPDX"):  # NO2, O3, CO, SO2 공식 컬럼명
        assert p in src, f"오염물질 컬럼 {p} 없음"


def test_correlation_analysis() -> None:
    """상관관계 분석 (.corr()) 포함."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert ".corr()" in src or "corr(" in src, "상관관계 분석 없음"


def test_hourly_functions_exist() -> None:
    """hourly_subway_ride() / hourly_air() 시간대별 집계 함수 존재."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "hourly_subway_ride" in src, "hourly_subway_ride 함수 없음"
    assert "hourly_air" in src, "hourly_air 함수 없음"


def test_output_figure_path() -> None:
    """outputs/figs/12_hourly_air_vs_subway.png 출력 경로."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "12_hourly_air_vs_subway" in src or "air_vs_subway" in src, \
        "그래프 출력 경로 없음"


def test_hypothesis_5_label() -> None:
    """가설 ⑤ 야외 대기-지하철 동조 분석 레이블."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "가설" in src and ("⑤" in src or "5" in src), "가설 ⑤ 레이블 없음"
