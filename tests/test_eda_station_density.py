"""eda_station_density.py 회귀 가드 (cycle 538).

역별 승차 밀도 분석 — MetroEyes PoC 설치 우선순위 선정 근거.
공공데이터: 서울 열린데이터광장 CardSubwayTime 202602.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "eda_station_density.py"

sys.path.insert(0, str(ROOT / "scripts"))


def test_script_exists() -> None:
    assert SCRIPT.exists(), f"스크립트 없음: {SCRIPT}"


def test_month_constant() -> None:
    src = SCRIPT.read_text(encoding="utf-8")
    assert '"202602"' in src or "'202602'" in src, "MONTH 202602 없음"


def test_top_n_defined() -> None:
    src = SCRIPT.read_text(encoding="utf-8")
    assert "TOP_N" in src, "TOP_N 상수 없음"


def test_min_daily_boarding_filter() -> None:
    """최소 일 탑승 필터 (스팸 역 제거)."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "MIN_DAILY_BOARDING" in src, "MIN_DAILY_BOARDING 필터 없음"


def test_daily_boarding_function() -> None:
    src = SCRIPT.read_text(encoding="utf-8")
    assert "daily_boarding_by_station" in src, "daily_boarding_by_station 함수 없음"


def test_top_stations_function() -> None:
    src = SCRIPT.read_text(encoding="utf-8")
    assert "top_stations" in src, "top_stations 함수 없음"


def test_deployment_priority_score_function() -> None:
    src = SCRIPT.read_text(encoding="utf-8")
    assert "deployment_priority_score" in src, "deployment_priority_score 함수 없음"


def test_output_json_path() -> None:
    src = SCRIPT.read_text(encoding="utf-8")
    assert "station_density_ranking" in src, "출력 JSON 경로 없음"


def test_get_on_nope_columns() -> None:
    """CardSubwayTime GET_ON_NOPE 컬럼 사용."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "GET_ON_NOPE" in src, "GET_ON_NOPE 컬럼 없음"


def test_metroeyes_poc_target_label() -> None:
    """MetroEyes PoC 설치 근거 레이블."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "metroeyes_poc_target" in src or "MetroEyes" in src, "MetroEyes PoC 레이블 없음"


def test_daily_boarding_returns_dataframe() -> None:
    from eda_station_density import load_cardsubwaytime, daily_boarding_by_station
    df = load_cardsubwaytime("202602")
    result = daily_boarding_by_station(df)
    assert len(result) > 0, "역 집계 결과 비어있음"
    assert "daily_boarding" in result.columns, "daily_boarding 컬럼 없음"


def test_top_stations_count() -> None:
    """TOP-N 역 수 ≤ TOP_N."""
    from eda_station_density import (
        load_cardsubwaytime,
        daily_boarding_by_station,
        top_stations,
        TOP_N,
    )
    df = load_cardsubwaytime("202602")
    density = daily_boarding_by_station(df)
    top = top_stations(density, TOP_N)
    assert len(top) <= TOP_N, f"TOP {TOP_N} 초과: {len(top)}"
    assert len(top) > 0, "TOP 역 결과 비어있음"


def test_total_flow_descending() -> None:
    """TOP 역 total_flow 내림차순 정렬."""
    from eda_station_density import (
        load_cardsubwaytime,
        daily_boarding_by_station,
        top_stations,
        TOP_N,
    )
    df = load_cardsubwaytime("202602")
    density = daily_boarding_by_station(df)
    top = top_stations(density, TOP_N)
    flows = top["total_flow"].tolist()
    assert flows == sorted(flows, reverse=True), "total_flow 내림차순 아님"
