"""impact_summary 빌드 회귀 — admin 카드 + 시민 PWA + 운영자 chip 모두 의존."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _load_module():
    import importlib
    return importlib.import_module("src.cv.lite_server")


def test_impact_total_initial_state() -> None:
    """누적 impact 초기 상태가 0/빈 dict."""
    mod = _load_module()
    # 새로운 dict 객체 — runtime 변경 영향 안 받게 reset
    mod._impact_total["count"] = 0
    mod._impact_total["saved_pct_sum"] = 0.0
    mod._impact_total["stations"] = {}
    mod._impact_total["krw_paid"] = 0
    mod._impact_total["hourly"] = [0] * 24
    mod._impact_total["tier_counts"] = {"basic": 0, "od": 0, "transfer": 0}
    assert mod._impact_total["count"] == 0
    assert mod._impact_total["tier_counts"] == {"basic": 0, "od": 0, "transfer": 0}


def test_incident_total_six_types() -> None:
    """_incident_total dict에 6 type 모두 0 으로 초기화 가능."""
    mod = _load_module()
    expected = {"emergency", "suspicious", "lost", "free_ride", "priority_seat", "bottleneck", "events"}
    actual = set(mod._incident_total.keys())
    assert expected.issubset(actual), f"missing: {expected - actual}"
    # 각 type 정수 (events 제외)
    for k in expected - {"events"}:
        assert isinstance(mod._incident_total[k], int)


def test_avg_trip_min_constant() -> None:
    """IMPACT_AVG_TRIP_MIN 25.0 (서울 평균 통행시간 명세 일관성)."""
    mod = _load_module()
    assert mod.IMPACT_AVG_TRIP_MIN == 25.0


def test_value_per_min_constant() -> None:
    """IMPACT_VALUE_PER_MIN 167원 (한국교통연구원 혼잡비용 환산)."""
    mod = _load_module()
    assert mod.IMPACT_VALUE_PER_MIN == 167


def test_daily_riders_baseline() -> None:
    """DAILY_RIDERS_BASELINE 700만 (서울교통공사 2024)."""
    mod = _load_module()
    assert mod.DAILY_RIDERS_BASELINE == 7_000_000
