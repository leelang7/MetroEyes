"""scripts/co2_correlation.py CO₂-인원 상관 단위 테스트 (cycle 522).

IDEA-3 Weak Supervision 명분 — 야외 대기 ↔ 지하철 통행 상관:
- correlate_pollutant(sub_pat, air_pat): Pearson r/p/n 반환
- hourly_subway_pattern(sw): 24시간 정규화 (pandas DataFrame 입력)
- hourly_air_pattern(air, col): 24시간 대기 평균 정규화

co2_correlation은 Windows에서 sys.stdout을 모듈 레벨에 교체 —
pytest stdout 보호 후 임포트.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")

from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# co2_correlation.py는 Windows에서 sys.stdout을 io.TextIOWrapper로 교체 —
# 교체 후 GC가 pytest 버퍼를 닫아 "I/O on closed file" 발생.
# platform을 'linux'로 스푸핑하면 if sys.platform == "win32" 블록이 실행 안 됨.
sys.modules.pop("co2_correlation", None)
with patch.object(sys, "platform", "linux"):
    from co2_correlation import (  # noqa: E402
        correlate_pollutant,
        hourly_subway_pattern,
        hourly_air_pattern,
    )


def _make_sw_df() -> "pd.DataFrame":
    """24시간 승하차 mock DataFrame."""
    data = {}
    for h in range(24):
        data[f"HR_{h}_GET_ON_NOPE"] = [100 + h * 10, 90 + h * 5]
        data[f"HR_{h}_GET_OFF_NOPE"] = [80 + h * 8, 70 + h * 4]
    return pd.DataFrame(data)


def _make_air_df() -> "pd.DataFrame":
    """24시간 대기 mock DataFrame."""
    hours = list(range(24)) * 3
    pm25 = [float(20 + h % 12) for h in hours]
    return pd.DataFrame({"hour": hours, "PM25": pm25})


def test_correlate_pollutant_keys() -> None:
    """correlate_pollutant() — r/p/n 키 존재."""
    sub = np.sin(np.linspace(0, 2 * np.pi, 24))
    air = np.sin(np.linspace(0, 2 * np.pi, 24))
    result = correlate_pollutant(sub, air)
    for key in ("r", "p", "n"):
        assert key in result, f"키 {key} 누락"


def test_correlate_pollutant_perfect_correlation() -> None:
    """동일 배열 → r ≈ 1.0."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    result = correlate_pollutant(x, x)
    assert result["r"] is not None
    assert abs(result["r"] - 1.0) < 1e-6, f"r={result['r']} ≠ 1.0"


def test_correlate_pollutant_p_value_range() -> None:
    """correlate_pollutant() — p value ∈ [0, 1]."""
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    y = x + np.random.default_rng(42).normal(0, 0.1, len(x))
    result = correlate_pollutant(x, y)
    assert 0.0 <= result["p"] <= 1.0, f"p={result['p']} 범위 벗어남"


def test_correlate_pollutant_nan_masked() -> None:
    """NaN 포함 배열 — 유효 샘플만 사용."""
    sub = np.array([1.0, 2.0, np.nan, 4.0, 5.0, 6.0])
    air = np.array([1.1, 2.1, 3.1, np.nan, 5.1, 6.1])
    result = correlate_pollutant(sub, air)
    assert result["n"] == 4, f"유효 샘플 {result['n']} ≠ 4"


def test_correlate_pollutant_few_samples() -> None:
    """유효 샘플 < 5 → r=None, p=None."""
    sub = np.array([1.0, np.nan, np.nan, np.nan, np.nan])
    air = np.array([1.0, np.nan, np.nan, np.nan, np.nan])
    result = correlate_pollutant(sub, air)
    assert result["r"] is None, "r가 None이어야 함 (샘플 < 5)"
    assert result["p"] is None, "p가 None이어야 함 (샘플 < 5)"


def test_hourly_subway_pattern_shape() -> None:
    """hourly_subway_pattern(sw) → shape (24,)."""
    sw = _make_sw_df()
    pat = hourly_subway_pattern(sw)
    assert pat.shape == (24,), f"shape {pat.shape} ≠ (24,)"


def test_hourly_subway_pattern_normalized() -> None:
    """hourly_subway_pattern(sw) → max ≤ 1.0."""
    sw = _make_sw_df()
    pat = hourly_subway_pattern(sw)
    assert pat.max() <= 1.0 + 1e-9, f"max {pat.max()} > 1.0"


def test_hourly_air_pattern_shape() -> None:
    """hourly_air_pattern(air, col) → shape (24,)."""
    air = _make_air_df()
    pat = hourly_air_pattern(air, "PM25")
    assert pat.shape == (24,), f"shape {pat.shape} ≠ (24,)"
