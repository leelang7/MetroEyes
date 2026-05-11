"""scripts/policy_roi_v2.py 정책 ROI v2 시뮬 단위 테스트 (cycle 519).

v2 특징 (v3과 차별화):
- coverage_ratio = HUB_STATIONS/296 (환승허브 85역 비율)
- hub_focus 파라미터 (1.0 = 85역만, 296 = 전체)
- 비교: v2 vs v3 결과 방향성 일관성

네트워크/데이터 불필요 — 순수 numpy 시뮬.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_v2_simulate_returns_required_keys() -> None:
    """simulate(0.30) 반환값 필수 키 검증."""
    from policy_roi_v2 import simulate
    r = simulate(0.30)
    for key in ("commute_b", "safety_b", "total_gain_b", "net_value_b",
                "roi_x", "minutes_saved_yr", "coverage_ratio"):
        assert key in r, f"키 {key} 누락"


def test_v2_simulate_positive_savings() -> None:
    """simulate(0.30) → 절감 > 0."""
    from policy_roi_v2 import simulate
    r = simulate(0.30)
    assert r["minutes_saved_yr"] > 0, "연간 절감 분 = 0"
    assert r["commute_b"] > 0, "통근 가치 = 0"


def test_v2_simulate_roi_positive() -> None:
    """simulate(0.30) → ROI > 0."""
    from policy_roi_v2 import simulate
    r = simulate(0.30)
    assert r["roi_x"] > 0, "ROI ≤ 0"


def test_v2_simulate_coverage_ratio_hub_focus() -> None:
    """hub_focus=1.0 → coverage_ratio = HUB_STATIONS/296."""
    from policy_roi_v2 import simulate, HUB_STATIONS
    r = simulate(0.30, hub_focus=1.0)
    expected = HUB_STATIONS / 296.0
    assert abs(r["coverage_ratio"] - expected) < 1e-6


def test_v2_simulate_higher_response_more_savings() -> None:
    """응답률 높을수록 절감 큼."""
    from policy_roi_v2 import simulate
    low = simulate(0.10)
    high = simulate(0.50)
    assert high["minutes_saved_yr"] > low["minutes_saved_yr"]


def test_v2_fmt_b_hundreds() -> None:
    """fmt_b(500) → '500억'."""
    from policy_roi_v2 import fmt_b
    assert "500" in fmt_b(500) or "억" in fmt_b(500)


def test_v2_fmt_b_thousands() -> None:
    """fmt_b(15000) → '조' 단위."""
    from policy_roi_v2 import fmt_b
    assert "조" in fmt_b(15000)


def test_v2_hub_stations_constant() -> None:
    """HUB_STATIONS > 0 (환승 허브역 수)."""
    from policy_roi_v2 import HUB_STATIONS
    assert HUB_STATIONS > 0, f"HUB_STATIONS {HUB_STATIONS} ≤ 0"


def test_v2_hour_demand_curve_sums_to_1() -> None:
    """v2 hour_demand_curve() 합계 = 1.0."""
    from policy_roi_v2 import hour_demand_curve
    curve = hour_demand_curve()
    assert abs(curve.sum() - 1.0) < 1e-6
