"""operator_web/index.html 운영자 지하철 콘솔 회귀 가드 (cycle 504).

핵심 기능:
- MetroEyes 브랜드 + 도메인 바 (subway)
- 4언어 토글 (ko/en/zh/ja) + I18N_OP 딕셔너리
- 데모 트리거 버튼 (demo-trigger)
- GPS 태그 + 역 피커 (station-picker)
- 임팩트 pill / 분산 pill / 차등 pill
- OD 분산 우선순위 스트립 / 환승 흐름 스트립
- LLM 어시스턴트 연동 (llm_assistant.js)
- 경고 배너 (alert-banner)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IDX = ROOT / "frontend" / "operator_web" / "index.html"


def _html() -> str:
    return IDX.read_text(encoding="utf-8")


def test_operator_subway_exists() -> None:
    """operator_web/index.html 존재."""
    assert IDX.is_file(), "operator_web/index.html 누락"


def test_operator_subway_brand() -> None:
    """MetroEyes 브랜드 + 지하철 운영자 표시."""
    html = _html()
    assert "MetroEyes" in html, "MetroEyes 브랜드 누락"
    assert "지하철" in html, "지하철 도메인 표시 누락"


def test_operator_subway_domain_bar() -> None:
    """domain-bar subway 클래스."""
    html = _html()
    assert "domain-bar subway" in html or 'class="domain-bar subway"' in html, \
        "subway 도메인 바 누락"


def test_operator_subway_demo_trigger() -> None:
    """demo-trigger 버튼 존재."""
    html = _html()
    assert "demo-trigger" in html, "demo-trigger 버튼 누락"
    assert "시연 모드" in html, "시연 모드 텍스트 누락"


def test_operator_subway_lang_toggle() -> None:
    """lang-toggle 버튼 + 4언어 지원."""
    html = _html()
    assert "lang-toggle" in html, "lang-toggle 버튼 누락"
    # I18N_OP 딕셔너리에 4언어 포함
    for lang in ("ko", "en", "zh", "ja"):
        assert f"'{lang}'" in html or f'"{lang}"' in html, f"{lang} 언어 코드 누락"


def test_operator_subway_i18n_flags() -> None:
    """4개 국기 이모지 포함 (언어 토글 식별용)."""
    html = _html()
    for flag in ("🇰🇷", "🇺🇸", "🇨🇳", "🇯🇵"):
        assert flag in html, f"{flag} 국기 이모지 누락"


def test_operator_subway_gps_tag() -> None:
    """GPS 태그 + gps-station 역명 표시 + 역 피커."""
    html = _html()
    assert "gps-tag" in html, "gps-tag element 누락"
    assert "gps-station" in html, "gps-station element 누락"
    assert "station-picker" in html, "station-picker 드롭다운 누락"


def test_operator_subway_impact_pill() -> None:
    """분산 임팩트 pill — impact-pill / impact-pill-cnt / impact-pill-roi."""
    html = _html()
    assert "impact-pill" in html, "impact-pill element 누락"
    assert "impact-pill-cnt" in html, "impact-pill-cnt 누락"
    assert "impact-pill-roi" in html, "impact-pill-roi 누락"


def test_operator_subway_dispersion_pill() -> None:
    """분산 효과 pill — sigma/peak."""
    html = _html()
    assert "dispersion-pill" in html or "op-dp-sigma" in html, "분산 효과 pill 누락"
    assert "op-dp-sigma" in html, "op-dp-sigma 누락"
    assert "op-dp-peak" in html, "op-dp-peak 누락"


def test_operator_subway_od_priority_strip() -> None:
    """OD 분산 우선순위 스트립."""
    html = _html()
    assert "od-priority-strip" in html, "od-priority-strip 누락"
    assert "od-rationale" in html, "od-rationale 누락"


def test_operator_subway_transfer_strip() -> None:
    """환승 흐름 우세 스트립."""
    html = _html()
    assert "op-tp-strip" in html, "op-tp-strip 누락"
    assert "op-tp-rationale" in html, "op-tp-rationale 누락"


def test_operator_subway_alert_banner() -> None:
    """경고 배너 (alert-banner) — 임계 사건 시 표시."""
    html = _html()
    assert "alert-banner" in html, "alert-banner 누락"
    assert "alert-banner-text" in html, "alert-banner-text 누락"


def test_operator_subway_navigation_links() -> None:
    """상단 내비 — 버스/실카메라/광고/시민앱/통합시연 링크."""
    html = _html()
    for href in ("bus.html", "realbev.html", "ad_pricing.html", "passenger_app/index.html", "demo.html"):
        assert href in html, f"내비 링크 {href} 누락"
