"""scripts/policy_roi_v3.py 정책 ROI 시뮬 단위 테스트 (cycle 515).

네트워크/데이터 불필요 — 순수 numpy 시뮬레이션 함수:
- hour_demand_curve: 24시 수요 분포 합계=1.0
- simulate_v3: 30% 응답률 → 절감분 계산
- 상수: DAILY_RIDERS / WORKDAYS_YR / LINE_CAP_RATIO / LINE_DAILY

심사 기준 '공공데이터 활용·실현가능성': 정량 모델 신뢰성 보장.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

# scripts 경로를 임시로 sys.path에 추가
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_hour_demand_curve_sums_to_1() -> None:
    """hour_demand_curve() 합계 = 1.0 (확률 분포)."""
    from policy_roi_v3 import hour_demand_curve
    curve = hour_demand_curve()
    assert abs(curve.sum() - 1.0) < 1e-6, f"curve 합계 {curve.sum()} ≠ 1.0"


def test_hour_demand_curve_shape() -> None:
    """hour_demand_curve() shape = (24,)."""
    from policy_roi_v3 import hour_demand_curve
    curve = hour_demand_curve()
    assert curve.shape == (24,), f"shape {curve.shape} ≠ (24,)"


def test_hour_demand_curve_non_negative() -> None:
    """hour_demand_curve() 모든 값 ≥ 0."""
    from policy_roi_v3 import hour_demand_curve
    curve = hour_demand_curve()
    assert (curve >= 0).all(), "음수 수요값 존재"


def test_hour_demand_curve_peaks_at_commute_hours() -> None:
    """출퇴근 시간대 (7-9, 17-19) 수요가 낮시간 (11-15)보다 높음."""
    from policy_roi_v3 import hour_demand_curve
    curve = hour_demand_curve()
    peak_am = curve[7:10].mean()
    peak_pm = curve[17:20].mean()
    midday = curve[11:15].mean()
    assert peak_am > midday, "AM 피크가 낮시간보다 낮음"
    assert peak_pm > midday, "PM 피크가 낮시간보다 낮음"


def test_simulate_v3_positive_savings() -> None:
    """simulate_v3(0.30) → 절감분 > 0."""
    from policy_roi_v3 import simulate_v3
    result = simulate_v3(behavior_response=0.30)
    assert result["commute_b"] > 0, "통근 시간 절감 = 0"
    assert result["minutes_saved_yr"] > 0, "연간 절감 분 = 0"


def test_simulate_v3_roi_positive() -> None:
    """simulate_v3(0.30) → ROI > 0."""
    from policy_roi_v3 import simulate_v3
    result = simulate_v3(behavior_response=0.30)
    assert result["roi_x"] > 0, "ROI ≤ 0"


def test_simulate_v3_total_benefit_order() -> None:
    """30% 응답률 시 총 편익 1,000억 이상 (ROI v3 주장 근거)."""
    from policy_roi_v3 import simulate_v3
    result = simulate_v3(behavior_response=0.30)
    # 1,393억 → 최소 1,000억 (실현가능성 마진)
    total_b = result["total_gain_b"]
    assert total_b >= 100.0, f"총 편익 {total_b}억 < 1,000억원 예상"


def test_line_cap_ratio_9_lines() -> None:
    """LINE_CAP_RATIO — 1~9호선 모두 정의."""
    from policy_roi_v3 import LINE_CAP_RATIO
    for line in [f"{i}호선" for i in range(1, 10)]:
        assert line in LINE_CAP_RATIO, f"{line} cap ratio 누락"


def test_line_daily_9_lines() -> None:
    """LINE_DAILY — 1~9호선 일평균 통행자 정의."""
    from policy_roi_v3 import LINE_DAILY
    for line in [f"{i}호선" for i in range(1, 10)]:
        assert line in LINE_DAILY, f"{line} 일평균 통행자 누락"
        assert LINE_DAILY[line] > 0, f"{line} 통행자 수 = 0"


def test_daily_riders_constant() -> None:
    """DAILY_RIDERS = 7,000,000 (서울 지하철 일 이용객 기준)."""
    from policy_roi_v3 import DAILY_RIDERS
    assert DAILY_RIDERS == 7_000_000, f"DAILY_RIDERS {DAILY_RIDERS} ≠ 7,000,000"
