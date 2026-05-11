"""scripts/train_occupancy.py melt_hourly 단위 테스트 (cycle 524).

melt_hourly(df): CardSubwayTime 48컬럼 → long format 변환.
입력 컬럼: SBWY_ROUT_LN_NM, STTN, HR_n_GET_ON/OFF_NOPE (n=0..23).
출력 컬럼: line_name, station, hour, on, off.

sklearn/joblib/matplotlib 모듈 레벨 임포트가 있어 importorskip으로 처리.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("sklearn")
pytest.importorskip("joblib")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _make_subway_df(n_stations: int = 3, lines: int = 2) -> "pd.DataFrame":
    """HR_n_GET_ON/OFF_NOPE 48컬럼 포함 mock DataFrame."""
    line_names = [f"{i+1}호선" for i in range(lines)]
    stations = [f"역{i}" for i in range(n_stations)]
    rows = []
    for line in line_names:
        for station in stations:
            row = {
                "SBWY_ROUT_LN_NM": line,
                "STTN": station,
                "USE_MM": "202602",
            }
            for h in range(24):
                row[f"HR_{h}_GET_ON_NOPE"] = float(100 + h * 50)
                row[f"HR_{h}_GET_OFF_NOPE"] = float(80 + h * 40)
            rows.append(row)
    return pd.DataFrame(rows)


def test_melt_hourly_returns_dataframe() -> None:
    """melt_hourly(df) → pd.DataFrame 반환."""
    from train_occupancy import melt_hourly
    df = _make_subway_df()
    result = melt_hourly(df)
    assert isinstance(result, pd.DataFrame), "DataFrame 반환 아님"


def test_melt_hourly_output_columns() -> None:
    """melt_hourly(df) → 필수 컬럼 (line_name, station, hour, on, off)."""
    from train_occupancy import melt_hourly
    result = melt_hourly(_make_subway_df())
    for col in ("line_name", "station", "hour", "on", "off"):
        assert col in result.columns, f"컬럼 {col} 누락"


def test_melt_hourly_hour_range() -> None:
    """melt_hourly() → hour ∈ [0, 23]."""
    from train_occupancy import melt_hourly
    result = melt_hourly(_make_subway_df())
    assert result["hour"].between(0, 23).all(), "hour 범위 벗어남"


def test_melt_hourly_on_nonneg() -> None:
    """melt_hourly() → on ≥ 0."""
    from train_occupancy import melt_hourly
    result = melt_hourly(_make_subway_df())
    assert (result["on"] >= 0).all(), "승차 음수 존재"


def test_melt_hourly_row_count() -> None:
    """melt_hourly() 행수 = stations × lines × 24 (모든 시간대)."""
    from train_occupancy import melt_hourly
    df = _make_subway_df(n_stations=3, lines=2)
    result = melt_hourly(df)
    expected = 3 * 2 * 24
    assert len(result) == expected, f"행수 {len(result)} ≠ {expected}"


def test_melt_hourly_preserves_lines() -> None:
    """melt_hourly() — line_name 값이 유지됨."""
    from train_occupancy import melt_hourly
    df = _make_subway_df(lines=2)
    result = melt_hourly(df)
    assert "1호선" in result["line_name"].values, "1호선 누락"
    assert "2호선" in result["line_name"].values, "2호선 누락"
