"""scripts/policy_roi.py (v1) 정책 ROI 시뮬 단위 테스트 (cycle 520).

v1 특징:
- Assumptions dataclass: 13개 파라미터
- simulate(a): commute / safety / ad / energy / total / cost / roi_multiple
- CONSERVATIVE / OPTIMISTIC 두 시나리오
- fmt_b(): 억 / 천억조 포맷

네트워크/데이터 불필요 — 순수 산술.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_simulate_conservative_keys() -> None:
    """simulate(CONSERVATIVE) 필수 키 검증."""
    from policy_roi import simulate, CONSERVATIVE
    r = simulate(CONSERVATIVE)
    for key in ("commute", "safety", "ad", "energy", "total", "cost",
                "payback_days", "roi_multiple"):
        assert key in r, f"키 {key} 누락"


def test_simulate_conservative_positive_benefits() -> None:
    """보수 시나리오 — 4가지 편익 모두 > 0."""
    from policy_roi import simulate, CONSERVATIVE
    r = simulate(CONSERVATIVE)
    assert r["commute"] > 0, "commute = 0"
    assert r["safety"] > 0, "safety = 0"
    assert r["ad"] > 0, "ad = 0"
    assert r["energy"] > 0, "energy = 0"


def test_simulate_conservative_total_positive() -> None:
    """보수 시나리오 — 총 가치 > 0."""
    from policy_roi import simulate, CONSERVATIVE
    r = simulate(CONSERVATIVE)
    assert r["total"] > 0, f"total {r['total']} ≤ 0"


def test_simulate_conservative_roi_positive() -> None:
    """보수 시나리오 — ROI > 0."""
    from policy_roi import simulate, CONSERVATIVE
    r = simulate(CONSERVATIVE)
    assert r["roi_multiple"] > 0, f"roi_multiple {r['roi_multiple']} ≤ 0"


def test_simulate_optimistic_gt_conservative() -> None:
    """낙관 시나리오 총 가치 > 보수."""
    from policy_roi import simulate, CONSERVATIVE, OPTIMISTIC
    c = simulate(CONSERVATIVE)
    o = simulate(OPTIMISTIC)
    assert o["total"] > c["total"], "낙관 총 가치 ≤ 보수"


def test_simulate_payback_days_positive() -> None:
    """보수 시나리오 — 투자 회수일 > 0."""
    from policy_roi import simulate, CONSERVATIVE
    r = simulate(CONSERVATIVE)
    assert r["payback_days"] > 0, "payback_days ≤ 0"


def test_fmt_b_hundreds() -> None:
    """fmt_b(100) → '100억'."""
    from policy_roi import fmt_b
    result = fmt_b(100)
    assert "100" in result and "억" in result, f"fmt_b(100)={result!r}"


def test_fmt_b_thousands() -> None:
    """fmt_b(15000) → '조' 포함."""
    from policy_roi import fmt_b
    result = fmt_b(15000)
    assert "조" in result, f"fmt_b(15000)={result!r}"


def test_conservative_assumptions_riders() -> None:
    """CONSERVATIVE.daily_riders_m = 7.0 (서울 지하철 기준)."""
    from policy_roi import CONSERVATIVE
    assert CONSERVATIVE.daily_riders_m == 7.0, \
        f"daily_riders_m {CONSERVATIVE.daily_riders_m} ≠ 7.0"


def test_optimistic_more_stations() -> None:
    """낙관 시나리오 배포 역수 > 보수 (확장형)."""
    from policy_roi import CONSERVATIVE, OPTIMISTIC
    assert OPTIMISTIC.rollout_stations > CONSERVATIVE.rollout_stations, \
        "낙관 배포 역수 ≤ 보수"
