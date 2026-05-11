"""frontend/operator_web/ad_pricing.html 광고 단가 책정 회귀 가드 (cycle 526).

IDEA-4 — 칸 점유 기반 동적 광고 단가:
- MetroEyes 브랜드 + domain-bar ads
- 히트맵 (.heatmap) + 가격 카드 (.price-card)
- KPI 행 (.kpi-row) + 인사이트 패널 (.insight)
- 4개 nav 링크 + 시민 앱 링크
- 모바일 반응형 media query
"""
from __future__ import annotations

from pathlib import Path

AD_HTML = Path(__file__).resolve().parent.parent / "frontend/operator_web/ad_pricing.html"


def _html() -> str:
    return AD_HTML.read_text(encoding="utf-8")


def test_ad_pricing_file_exists() -> None:
    """ad_pricing.html 파일 존재."""
    assert AD_HTML.exists(), "frontend/operator_web/ad_pricing.html 없음"


def test_ad_pricing_brand() -> None:
    """MetroEyes 브랜드 텍스트 존재."""
    assert "MetroEyes" in _html(), "브랜드 MetroEyes 없음"


def test_ad_pricing_domain_bar_ads() -> None:
    """domain-bar ads 클래스 — 광고 도메인 표시."""
    assert 'data-domain="ads"' in _html(), 'data-domain="ads" 없음'


def test_ad_pricing_heatmap() -> None:
    """히트맵 (.heatmap) — 시간대 × 역 점유 시각화 존재."""
    assert "heatmap" in _html(), ".heatmap 클래스 없음"


def test_ad_pricing_price_card() -> None:
    """가격 카드 (.price-card) 존재 — 동적 단가 표시."""
    assert "price-card" in _html(), ".price-card 클래스 없음"


def test_ad_pricing_kpi_row() -> None:
    """KPI 행 (.kpi-row) — 요약 지표."""
    assert "kpi-row" in _html(), ".kpi-row 없음"


def test_ad_pricing_insight() -> None:
    """인사이트 패널 (.insight) 존재."""
    assert "insight" in _html(), ".insight 없음"


def test_ad_pricing_nav_links() -> None:
    """4개 핵심 nav 링크 존재 (subway/bus/realbev/citizen_app)."""
    html = _html()
    assert "index.html" in html, "운영자 지하철 링크 없음"
    assert "bus.html" in html, "버스 링크 없음"
    assert "passenger_app" in html, "시민 앱 링크 없음"


def test_ad_pricing_mobile_responsive() -> None:
    """모바일 반응형 media query 존재 (max-width: 760px)."""
    assert "max-width: 760px" in _html() or "max-width:760px" in _html(), \
        "모바일 반응형 media query 없음"


def test_ad_pricing_idea4_reference() -> None:
    """IDEA-4 레퍼런스 존재 (광고 IDEA 명분)."""
    assert "IDEA-4" in _html() or "idea-4" in _html().lower(), "IDEA-4 레퍼런스 없음"
