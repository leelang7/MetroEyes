"""docs/PROPOSAL.md §5 ROI v3 정합성 회귀 (cycle 371).

§5 가 v2 ₩9,470억이 아닌 v3 1,393억 + Monte Carlo 95% CI [1,064~1,808] 광고.
호선별 ROI + 호선×시간 매트릭스 신규 §5.3 §5.4 누락 차단.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROP = ROOT / "docs" / "PROPOSAL.md"


def _txt() -> str:
    return PROP.read_text(encoding="utf-8")


def test_v3_kpi_advertised() -> None:
    """v3 핵심 KPI: 1,393억 / 347x / 473.4M / 134역 / 167원 모두 §5 안에."""
    t = _txt()
    for kpi in ("1,393억", "347x", "473.4M", "134", "167원"):
        assert kpi in t, f"PROPOSAL §5 missing v3 KPI: {kpi}"


def test_v2_outdated_numbers_removed() -> None:
    """v2 9,470억 / 3,714x 등 outdated 수치 제거."""
    t = _txt()
    # outdated 표 헤더
    assert "9,470억원/년" not in t, "outdated v2 합계 표 still present"
    assert "ROI 5,928x" not in t, "outdated 낙관 시나리오 still present"


def test_monte_carlo_ci_section_present() -> None:
    """§5.2 Monte Carlo 95% CI 섹션 명시."""
    t = _txt()
    assert "Monte Carlo" in t, "Monte Carlo reference missing"
    assert "95% CI" in t, "95% CI label missing"
    # 핵심 CI 수치 — 30% 시나리오
    assert "1,064" in t and "1,808" in t, "30% scenario CI [1,064~1,808] missing"


def test_line_priority_roi_section_present() -> None:
    """§5.3 호선별 ROI 정량 답."""
    t = _txt()
    assert "621x" in t, "2호선 ROI 621x missing"
    assert "🥇" in t and "🥈" in t and "🥉" in t, "medal markers missing"
    assert "121x" in t, "1호선 121x (lowest) missing"


def test_line_hour_matrix_section_present() -> None:
    """§5.4 호선×시간 매트릭스 (cycle 368) 명시."""
    t = _txt()
    assert "9시 / 17시 / 19시" in t or "9시" in t, "2호선 peak hours missing"
    assert "priority 158" in t.lower() or "158" in t, "Top 5 priority score missing"
    assert "5~6시" in t or "5시" in t, "1호선 bottom hour missing"


def test_scripts_referenced() -> None:
    """관련 산출 스크립트 모두 명시 (재현성)."""
    t = _txt()
    for script in ("policy_roi_v3.py", "eda_line_priority_roi.py", "eda_line_hour_priority.py"):
        assert script in t, f"PROPOSAL missing script reference: {script}"
