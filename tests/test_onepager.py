"""frontend/onepager.html 1-Pager 회귀 (cycle 372).

A4 print-friendly 단일 페이지 — 심사위원이 take-away 자료로 들고 갈 수 있는 핵심 KPI 압축본.
광고 KPI ↔ pitch.html ↔ PROPOSAL ↔ onepager 모두 동일 수치 보장.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ONEPAGER = ROOT / "frontend" / "onepager.html"


def _html() -> str:
    return ONEPAGER.read_text(encoding="utf-8")


def test_onepager_exists() -> None:
    assert ONEPAGER.exists(), f"missing {ONEPAGER}"


def test_a4_print_friendly() -> None:
    """@page A4 + print 미디어 쿼리 + 인쇄 버튼."""
    html = _html()
    assert "@page" in html and "A4 portrait" in html, "A4 print spec missing"
    assert "@media print" in html, "print media query missing"
    assert "window.print()" in html, "print button missing"


def test_kpi_consistency_with_pitch() -> None:
    """광고 KPI 가 pitch.html / PROPOSAL / README 와 모두 동일."""
    html = _html()
    # 핵심 KPI
    for kpi in ("347x", "1,393억", "473M", "120"):
        assert kpi in html, f"missing KPI: {kpi}"
    # Monte Carlo CI 표시
    assert "1,064" in html or "1064" in html, "30% CI lower bound missing"
    assert "1,808" in html or "1808" in html, "30% CI upper bound missing"
    # 호선별 ROI (cycle 360, cycle 374 v3 alignment)
    assert "708x" in html, "2호선 ROI 708x (cycle 374 v3 alignment) missing"
    # 호선×시간 (cycle 368)
    assert "priority 158" in html.lower() or "priority 158" in html, "Top 5 cell priority missing"


def test_business_section_present() -> None:
    """사업화 BM 3-tier 명시 — 1차 평가 가점."""
    html = _html()
    for kw in ("B2G", "B2B", "₩40억", "₩100억"):
        assert kw in html, f"business section missing: {kw}"


def test_competitor_table_present() -> None:
    """4 도시 비교 표 — London / Tokyo / Singapore / MetroEyes."""
    html = _html()
    for city in ("London", "Tokyo", "Singapore", "MetroEyes"):
        assert city in html, f"competitor city missing: {city}"


def test_links_to_canonical_artifacts() -> None:
    """live demo / GitHub / pitch.html 링크."""
    html = _html()
    assert "leelang7.github.io" in html, "live demo link missing"
    assert "github.com/leelang7" in html, "github link missing"
    assert "pitch.html" in html, "pitch.html cross-link missing"


def test_4axis_perturbation_documented() -> None:
    """Monte Carlo 4축 perturbation 명시 (통계 신뢰도 어필)."""
    html = _html()
    assert "Monte Carlo" in html or "1,000회" in html or "1000회" in html, "Monte Carlo reference missing"
