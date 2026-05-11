"""scripts/eda_co2_savings.py CO₂ 절감 모델 단위 테스트 (cycle 518).

ESG 정량 EDA — 심사 기준 '사회적 가치' 핵심 수치:
- co2_per_action_kg: 분산 1회 CO₂ 절감 계산
- annual_co2_savings_kg: 1년치 절감 추정 (ultra/standard 두 시나리오)
- ADVERTISED_VALUE_KG: 광고 기재 0.012 kg 보수 기준 검증

네트워크/데이터 불필요 — 순수 수식.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_co2_per_action_default_positive() -> None:
    """co2_per_action_kg() 기본값 > 0."""
    from eda_co2_savings import co2_per_action_kg
    v = co2_per_action_kg()
    assert v > 0, "기본 CO₂ 절감 = 0 이하"


def test_co2_per_action_ultra_conservative() -> None:
    """ultra-conservative (CAR_AVOIDANCE_ULTRA) → ≈ 0.012 kg."""
    from eda_co2_savings import co2_per_action_kg, CAR_AVOIDANCE_ULTRA, ADVERTISED_VALUE_KG
    v = co2_per_action_kg(rate=CAR_AVOIDANCE_ULTRA)
    # 광고 기재 0.012 ± 10% 이내
    assert abs(v - ADVERTISED_VALUE_KG) / ADVERTISED_VALUE_KG < 0.10, \
        f"ultra-conservative {v:.4f} kg ≠ 광고 기재 {ADVERTISED_VALUE_KG} kg"


def test_co2_per_action_standard_gt_ultra() -> None:
    """standard > ultra-conservative (5배 이상)."""
    from eda_co2_savings import co2_per_action_kg, CAR_AVOIDANCE_STD, CAR_AVOIDANCE_ULTRA
    std = co2_per_action_kg(rate=CAR_AVOIDANCE_STD)
    ultra = co2_per_action_kg(rate=CAR_AVOIDANCE_ULTRA)
    assert std > ultra * 3, f"standard {std} < ultra {ultra} × 3배"


def test_annual_co2_returns_required_fields() -> None:
    """annual_co2_savings_kg 반환값에 필수 필드 존재."""
    from eda_co2_savings import annual_co2_savings_kg
    r = annual_co2_savings_kg(0.30)
    for field in ("co2_yr_kg", "co2_yr_t", "actions_yr", "co2_per_action_kg",
                  "equivalent_persons_yr", "scenario"):
        assert field in r, f"필드 {field} 누락"


def test_annual_co2_ultra_smaller_than_standard() -> None:
    """ultra < standard (보수 기준이 더 작아야)."""
    from eda_co2_savings import annual_co2_savings_kg
    ultra = annual_co2_savings_kg(0.30, scenario="ultra")
    std = annual_co2_savings_kg(0.30, scenario="standard")
    assert ultra["co2_yr_kg"] < std["co2_yr_kg"], "ultra >= standard CO₂ 절감량"


def test_annual_co2_positive_savings() -> None:
    """30% 응답률 → CO₂ 절감 > 0."""
    from eda_co2_savings import annual_co2_savings_kg
    r = annual_co2_savings_kg(0.30)
    assert r["co2_yr_kg"] > 0
    assert r["actions_yr"] > 0


def test_annual_co2_scale_with_response_rate() -> None:
    """응답률 높을수록 절감 더 큼."""
    from eda_co2_savings import annual_co2_savings_kg
    low = annual_co2_savings_kg(0.10)
    high = annual_co2_savings_kg(0.50)
    assert high["co2_yr_kg"] > low["co2_yr_kg"], "응답률 높을수록 절감 커야"


def test_constants_commute_km() -> None:
    """COMMUTE_KM = 8.4 (서울 평균 통근 거리)."""
    from eda_co2_savings import COMMUTE_KM
    assert COMMUTE_KM == 8.4, f"COMMUTE_KM {COMMUTE_KM} ≠ 8.4"


def test_constants_daily_riders() -> None:
    """DAILY_RIDERS = 7,000,000."""
    from eda_co2_savings import DAILY_RIDERS
    assert DAILY_RIDERS == 7_000_000


def test_constants_advertised_value() -> None:
    """ADVERTISED_VALUE_KG = 0.012 (광고 ultra-conservative baseline)."""
    from eda_co2_savings import ADVERTISED_VALUE_KG
    assert ADVERTISED_VALUE_KG == 0.012, f"광고 기재값 {ADVERTISED_VALUE_KG} ≠ 0.012"
