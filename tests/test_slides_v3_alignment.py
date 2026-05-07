"""docs/SLIDES_DECK.md + SLIDES.html v3 정합성 회귀 (cycle 373).

PROPOSAL과 같이 SLIDES도 v2 9,470억 outdated → v3 1,393억 + Monte Carlo CI 광고.
대학 발표 자료 (Hancom/PDF) 가 광고 KPI ↔ 실제 ROI v3 와 일치하도록 보장.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "docs" / "SLIDES_DECK.md"
SLIDES = ROOT / "docs" / "SLIDES.html"


def _deck() -> str:
    return DECK.read_text(encoding="utf-8")


def _slides() -> str:
    return SLIDES.read_text(encoding="utf-8")


def test_deck_v3_kpi_present() -> None:
    """SLIDES_DECK 에 v3 핵심 KPI."""
    t = _deck()
    assert "1,393억" in t, "deck missing v3 1,393억"
    assert "347" in t and ("배" in t or "x" in t.lower() or "×" in t), "deck missing 347x"
    assert "Monte Carlo" in t, "deck missing Monte Carlo reference"


def test_deck_v2_outdated_removed() -> None:
    """SLIDES_DECK 에서 v2 9,470억 / 3,714× 제거."""
    t = _deck()
    # 헤드라인 / 빅 넘버 자리에서 outdated 사라져야 함
    assert "9,470억 사회적" not in t, "outdated v2 headline still present"
    assert "ROI 3,714×" not in t and "ROI 3,714배" not in t, "outdated ROI 3,714 still present"


def test_slides_html_v3_kpi_present() -> None:
    """SLIDES.html 도 v3 KPI 광고."""
    t = _slides()
    assert "1,393" in t, "slides.html missing v3 1,393"
    assert "347" in t, "slides.html missing 347"
    assert "Monte Carlo" in t or "monte carlo" in t.lower(), "slides.html missing Monte Carlo"
    # 95% CI band
    assert "1,064" in t and "1,808" in t, "slides.html 95% CI bounds missing"


def test_slides_html_v2_outdated_removed() -> None:
    """SLIDES.html 에서 v2 outdated 빅 넘버 제거."""
    t = _slides()
    # big-num em 안의 9,470 제거
    assert "<em>9,470</em>" not in t, "outdated <em>9,470</em> still present"
    assert "ROI 3,714" not in t and "3,714<span" not in t, "outdated ROI 3,714 still present"


def test_slides_html_line_priority_referenced() -> None:
    """슬라이드 19에 호선별 ROI (cycle 360, cycle 374 v3 alignment) 명시."""
    t = _slides()
    assert "708" in t, "2호선 ROI 708x (cycle 374 v3 alignment) missing"
    assert "2호선" in t, "Line 2 reference missing"


def test_slides_html_line_hour_top5_referenced() -> None:
    """슬라이드 19에 호선×시간 Top 5 (cycle 368) 명시."""
    t = _slides()
    assert "158" in t, "Top 5 priority score 158 missing"
    assert "9/17/19" in t or "9시" in t, "2호선 peak hours missing"
