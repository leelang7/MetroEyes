"""정책 ROI v3 회귀 테스트 — README/pitch.html에 광고된 핵심 수치 가드.

- 응답률 30% → 순 사회적 가치 1,393억/년, ROI 347x
- 절감 시간 473M+분/년
- 2호선 단독 ~157M분/년 (전체의 30% 이상)

검증 실패 시 README/pitch.html 광고된 수치와 코드가 어긋남.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.policy_roi_v3 import LINE_DAILY, simulate_v3   # noqa: E402


def test_roi_30pct_headline_kpi() -> None:
    """응답률 30% 시 README/pitch에 광고된 핵심 KPI 수치 일치."""
    r = simulate_v3(0.30)
    # 순 사회적 가치 1,393억/년 ± 1% (반올림 노이즈)
    net_b = r["net_value_b"]
    assert 1370 <= net_b <= 1420, f"net_value_b={net_b:.1f}억 — README says 1,393억"
    # ROI 347x ± 5x
    roi_x = r["roi_x"]
    assert 340 <= roi_x <= 355, f"roi_x={roi_x:.0f} — README says 347x"
    # 절감 분/년 473M+
    minutes = r["minutes_saved_yr"] / 1e6
    assert 465 <= minutes <= 485, f"minutes_saved_yr={minutes:.1f}M — README says 473.4M"


def test_line2_dominance() -> None:
    """2호선이 전체 절감의 30%+ 차지 (README '2호선 단독 157M분 절감')."""
    import numpy as np
    r = simulate_v3(0.30)
    save_matrix = np.array(r["save_matrix"])
    lines = r["lines"]
    line2_idx = lines.index("2호선")
    line2_total = save_matrix[line2_idx].sum() / 1e6
    grand_total = save_matrix.sum() / 1e6
    assert 150 <= line2_total <= 165, f"line2 total={line2_total:.1f}M — README says 157M"
    share = line2_total / grand_total
    assert share >= 0.30, f"line2 share={share:.1%} — should be 30%+"


def test_5_scenarios_monotonic() -> None:
    """응답률 5/15/30/50/70%에서 net_value_b가 monotonic 증가."""
    nets = [simulate_v3(r)["net_value_b"] for r in (0.05, 0.15, 0.30, 0.50, 0.70)]
    for i in range(len(nets) - 1):
        assert nets[i] < nets[i + 1], f"non-monotonic at idx {i}: {nets}"


def test_infra_134_stations() -> None:
    """README '인프라 4억 (134역 우선)' — n_stations_priority 일치."""
    r = simulate_v3(0.30)
    assert r["n_stations_priority"] == 134, f"n_stations_priority={r['n_stations_priority']} — README says 134"


def test_lines_count_9() -> None:
    """1~9호선 정확히 9개."""
    assert len(LINE_DAILY) == 9
    expected = {f"{i}호선" for i in range(1, 10)}
    assert set(LINE_DAILY.keys()) == expected
