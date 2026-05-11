"""poc_impact_estimate.py 회귀 가드 (cycle 534).

PoC 기대효과 정량 추정 — 1호선 25역 × 6개월.
심사 '실현가능성' 점수 핵심 근거: σ −9%, ₩136억/년 사회가치 정량화.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

SCRIPT = ROOT / "scripts" / "poc_impact_estimate.py"


def test_script_exists() -> None:
    assert SCRIPT.exists(), f"스크립트 없음: {SCRIPT}"


def test_response_rate_30_pct() -> None:
    """RESPONSE_RATE = 0.30 (policy_roi_v3 동일 기준)."""
    from poc_impact_estimate import RESPONSE_RATE
    assert RESPONSE_RATE == 0.30


def test_sigma_reduction_9_pct() -> None:
    """σ 감소 9% (eda_dispersion_sim 실증 기반)."""
    from poc_impact_estimate import SIGMA_REDUCTION
    assert SIGMA_REDUCTION == pytest.approx(0.09, abs=0.001)


def test_poc_stations_25() -> None:
    """PoC 대상 역 25개."""
    from poc_impact_estimate import POC_STATIONS
    assert POC_STATIONS == 25


def test_poc_commuter_time_savings_positive() -> None:
    """보딩 시간 절감 man-hours/일 > 0."""
    from poc_impact_estimate import poc_commuter_time_savings
    r = poc_commuter_time_savings()
    assert r["saved_hours_per_day"] > 0
    assert r["daily_responders"] > 0


def test_poc_commuter_responders_formula() -> None:
    """응답자 = 1호선 일 승객 × 커버리지 × 응답률."""
    from poc_impact_estimate import (
        LINE1_DAILY_RIDERS, POC_COVERAGE_RATIO, RESPONSE_RATE,
        poc_commuter_time_savings,
    )
    r = poc_commuter_time_savings()
    expected = int(LINE1_DAILY_RIDERS * POC_COVERAGE_RATIO * RESPONSE_RATE)
    assert abs(r["daily_responders"] - expected) <= 1


def test_social_value_annual_positive() -> None:
    """연간 사회가치 > 0 (₩)."""
    from poc_impact_estimate import poc_commuter_time_savings, poc_social_value_annual_krw
    ts = poc_commuter_time_savings()
    sv = poc_social_value_annual_krw(ts["saved_hours_per_day"])
    assert sv > 0


def test_social_value_exceeds_10bn_krw() -> None:
    """PoC 사회가치 > ₩100억 (최소 신뢰성 기준)."""
    from poc_impact_estimate import poc_commuter_time_savings, poc_social_value_annual_krw
    ts = poc_commuter_time_savings()
    sv = poc_social_value_annual_krw(ts["saved_hours_per_day"])
    assert sv >= 10_000_000_000, f"연간 사회가치 {sv/1e8:.1f}억 < 100억 — 가정값 확인 필요"


def test_ad_revenue_positive() -> None:
    """광고 Rev share 수익 > 0."""
    from poc_impact_estimate import poc_ad_revenue_annual_krw
    assert poc_ad_revenue_annual_krw() > 0


def test_main_returns_dict_with_required_keys() -> None:
    """main() 반환 dict에 핵심 KPI 키 존재."""
    from poc_impact_estimate import main
    result = main()
    for key in ("annual_social_value_krw", "sigma_reduction_pct", "daily_responders", "poc_stations"):
        assert key in result, f"결과 dict에 {key} 없음"


def test_sigma_reduction_pct_in_output() -> None:
    """결과 dict의 sigma_reduction_pct == 9.0."""
    from poc_impact_estimate import main
    result = main()
    assert result["sigma_reduction_pct"] == pytest.approx(9.0, abs=0.1)


import pytest
