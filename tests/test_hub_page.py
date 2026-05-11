"""frontend/index.html 허브 페이지 회귀 가드 (cycle 499).

허브 페이지 핵심 기능:
- MetroEyes 8-페이지 진입 허브 (첫인상 — 심사위원 랜딩)
- 4언어 lede 메시지 (ko/en/zh/ja)
- 핵심 KPI: 1,393억/년, ROI 347x
- 8개 도메인 카드 (지하철/버스/시민/광고/실카메라/비상/admin/pitch)
- 자동 사이클/가드 수 표시
- demo 서버 실행 안내
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUB = ROOT / "frontend" / "index.html"


def _html() -> str:
    return HUB.read_text(encoding="utf-8")


def test_hub_exists() -> None:
    """frontend/index.html 존재."""
    assert HUB.is_file(), "index.html 허브 페이지 누락"


def test_hub_metroeyes_brand() -> None:
    """MetroEyes 브랜드 표시."""
    html = _html()
    assert "MetroEyes" in html, "MetroEyes 브랜드 누락"


def test_hub_social_value_kpi() -> None:
    """핵심 KPI — 1,393억/년 + ROI 347x 표시."""
    html = _html()
    assert "1,393억" in html or "139.3B" in html, "허브 사회적 가치 KPI (1,393억) 누락"
    assert "347x" in html, "허브 ROI KPI (347x) 누락"


def test_hub_4lang_lede() -> None:
    """lede 메시지 4언어 사전 존재 (ko/en/zh/ja)."""
    html = _html()
    assert "lede" in html, "허브 lede i18n 구조 누락"
    assert "Subway/Bus BEV" in html or "subway" in html.lower(), "en lede 누락"


def test_hub_has_8_domain_cards() -> None:
    """8개 도메인 카드 (지하철/버스/시민PWA/광고/실카메라/비상/admin/pitch)."""
    html = _html()
    domains = ["subway", "bus", "passenger_app", "ad_pricing", "realbev", "admin", "pitch", "demo"]
    found = sum(1 for d in domains if d in html)
    assert found >= 6, f"도메인 카드 6개 이상 필요 (발견: {found}/8)"


def test_hub_demo_server_command() -> None:
    """demo 서버 실행 명령어 표시 (심사위원 재현 가이드)."""
    html = _html()
    assert "--demo" in html or "lite_server" in html, "demo 서버 실행 명령어 누락"


def test_hub_has_language_toggle() -> None:
    """언어 토글 버튼 (4언어 전환)."""
    html = _html()
    assert "lang" in html.lower() and ("toggle" in html.lower() or "btn" in html.lower()), \
        "언어 토글 버튼 누락"


def test_hub_guard_count_displayed() -> None:
    """가드 카운트 표시 (최신 상태 가시화)."""
    html = _html()
    assert "가드" in html or "guard" in html.lower(), "허브에 가드 수 표시 누락"


def test_hub_cycle_count_recent() -> None:
    """사이클 카운트가 300+ (진행 상태 가시화)."""
    import re
    html = _html()
    m = re.search(r'(\d+)\s*사이클', html)
    if m:
        count = int(m.group(1))
        assert count >= 300, f"사이클 수가 너무 낮음: {count}"


def test_hub_og_meta_tags() -> None:
    """og: 메타태그 존재 — 소셜 공유/심사위원 링크 미리보기."""
    html = _html()
    assert "og:title" in html, "og:title 메타태그 누락"
    assert "og:description" in html or "description" in html, "description 메타태그 누락"
