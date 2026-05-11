"""scripts/eda_line_carload.py 호선 점유 EDA 단위 테스트 (cycle 523).

순수 상수 + pandas mock — 데이터파일 불필요:
- LINE_CARS: 17개 호선 차량 수
- LINE_CAPACITY: 17개 호선 정원
- LINE_HEADWAY_MIN: 9호선 배차 간격
- estimate_carload(df): mock DataFrame → 점유율 추정 DataFrame

MetroEyes '칸 컬럼 부재' 골든 인사이트의 수식 신뢰성 검증.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _make_mock_df() -> "pd.DataFrame":
    """estimate_carload() 호환 최소 mock DataFrame."""
    hours = list(range(5, 24))
    rows = []
    for line in ["2호선", "9호선"]:
        for station in ["강남", "선릉"]:
            row = {"SBWY_ROUT_LN_NM": line, "STTN": station}
            for h in hours:
                row[f"HR_{h}_GET_ON_NOPE"] = 10000 + h * 500
                row[f"HR_{h}_GET_OFF_NOPE"] = 9000 + h * 400
            rows.append(row)
    return pd.DataFrame(rows)


def test_line_cars_count() -> None:
    """LINE_CARS — 17개 호선 정의."""
    from eda_line_carload import LINE_CARS
    assert len(LINE_CARS) == 17, f"호선 수 {len(LINE_CARS)} ≠ 17"


def test_line_cars_9_main_lines() -> None:
    """LINE_CARS — 1~9호선 모두 포함."""
    from eda_line_carload import LINE_CARS
    for i in range(1, 10):
        assert f"{i}호선" in LINE_CARS, f"{i}호선 누락"


def test_line_cars_values_positive() -> None:
    """LINE_CARS 차량 수 모두 > 0."""
    from eda_line_carload import LINE_CARS
    for line, n in LINE_CARS.items():
        assert n > 0, f"{line} cars = 0"


def test_line_capacity_count() -> None:
    """LINE_CAPACITY — 17개 호선 정의."""
    from eda_line_carload import LINE_CAPACITY
    assert len(LINE_CAPACITY) == 17, f"정원 호선 수 {len(LINE_CAPACITY)} ≠ 17"


def test_line_capacity_values_positive() -> None:
    """LINE_CAPACITY 정원 모두 > 0."""
    from eda_line_carload import LINE_CAPACITY
    for line, cap in LINE_CAPACITY.items():
        assert cap > 0, f"{line} capacity = 0"


def test_line_headway_9_main_lines() -> None:
    """LINE_HEADWAY_MIN — 1~9호선 정의."""
    from eda_line_carload import LINE_HEADWAY_MIN
    for i in range(1, 10):
        assert f"{i}호선" in LINE_HEADWAY_MIN, f"{i}호선 배차 간격 누락"


def test_line_headway_values_positive() -> None:
    """LINE_HEADWAY_MIN — 배차 간격 모두 > 0."""
    from eda_line_carload import LINE_HEADWAY_MIN
    for line, hw in LINE_HEADWAY_MIN.items():
        assert hw > 0, f"{line} headway = 0"


def test_estimate_carload_returns_dataframe() -> None:
    """estimate_carload(df) → pd.DataFrame 반환."""
    from eda_line_carload import estimate_carload
    mock_df = _make_mock_df()
    result = estimate_carload(mock_df)
    assert isinstance(result, pd.DataFrame), "DataFrame 반환 아님"


def test_estimate_carload_columns() -> None:
    """estimate_carload(df) → 필수 컬럼 존재."""
    from eda_line_carload import estimate_carload
    result = estimate_carload(_make_mock_df())
    for col in ("line", "hour", "occ_pct", "trains_per_h"):
        assert col in result.columns, f"컬럼 {col} 누락"


def test_estimate_carload_occ_pct_nonneg() -> None:
    """estimate_carload() — occ_pct ≥ 0."""
    from eda_line_carload import estimate_carload
    result = estimate_carload(_make_mock_df())
    assert (result["occ_pct"] >= 0).all(), "음수 점유율 존재"
