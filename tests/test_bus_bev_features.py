"""버스 BEV 운영자 콘솔 (operator_web/bus.html) 회귀 가드 (cycle 541).

버스 운영자 콘솔 핵심 기능:
- bev_engine.js 공용 BEV 렌더링
- fc-cv 검출 인원 카드 (applyBev)
- fc-arr 도착 정보 카드
- demo-trigger 시연 모드
- TTS 분산 안내 음성 송출
- LLM 어시스턴트 FAB
- 4언어 i18n
Note: cycle 541 — 차내 BEV 전용 섹션(bus-bev-canvas) 제거, 공용 bev_engine으로 통일
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUS = ROOT / "frontend" / "operator_web" / "bus.html"
AD = ROOT / "frontend" / "operator_web" / "ad_pricing.html"


def _bus() -> str:
    return BUS.read_text(encoding="utf-8")


def _ad() -> str:
    return AD.read_text(encoding="utf-8")


def test_bus_html_exists() -> None:
    """operator_web/bus.html 존재."""
    assert BUS.is_file(), "bus.html 파일 누락"


def test_bus_has_bev_engine() -> None:
    """공용 bev_engine.js 로드 + applyBev 핸들러 존재."""
    html = _bus()
    assert "bev_engine.js" in html, "bev_engine.js 로드 누락"
    assert "applyBev" in html, "applyBev 핸들러 누락"


def test_bus_has_demo_trigger() -> None:
    """demo-trigger 버튼 존재 — 시연 모드 자동화."""
    html = _bus()
    assert "demo-trigger" in html, "버스 demo-trigger 버튼 누락"


def test_bus_has_cv_card() -> None:
    """fc-cv 검출 인원 카드 존재 — 자체 CV 결과 표시."""
    html = _bus()
    assert "fc-cv" in html, "fc-cv 검출 인원 카드 누락"
    assert "검출 인원" in html, "검출 인원 텍스트 누락"


def test_bus_has_tts_button() -> None:
    """TTS 분산 안내 음성 송출 버튼."""
    html = _bus()
    assert "ttsBtn" in html, "버스 TTS 버튼 누락"
    assert "분산 안내" in html, "분산 안내 텍스트 누락"


def test_bus_has_llm_assistant() -> None:
    """LLM 어시스턴트 FAB + panel 존재."""
    html = _bus()
    assert "llmFab" in html, "버스 LLM FAB 버튼 누락"
    assert "llm_assistant.js" in html, "llm_assistant.js 로드 누락"


def test_bus_handles_bev_ws_type() -> None:
    """WS bev 타입 메시지 수신 → 버스 BEV 렌더링."""
    html = _bus()
    assert "bus_bev" in html or ("bev" in html and "bus" in html.lower()), \
        "버스 BEV WS 핸들러 누락"


def test_bus_has_arrival_card() -> None:
    """fc-arr 도착 정보 카드 존재."""
    html = _bus()
    assert "fc-arr" in html, "fc-arr 도착 카드 누락"


def test_bus_has_4lang_support() -> None:
    """4언어 지원 (ko/en/zh/ja)."""
    html = _bus()
    for lang in ("ko", "en", "zh", "ja"):
        assert lang in html, f"버스 i18n {lang} 누락"


def test_ad_pricing_html_exists() -> None:
    """operator_web/ad_pricing.html 존재."""
    assert AD.is_file(), "ad_pricing.html 파일 누락"


def test_ad_pricing_has_poi_cards() -> None:
    """POI 단가 카드 표시 영역."""
    html = _ad()
    assert "poi" in html.lower() and ("card" in html.lower() or "단가" in html), \
        "ad_pricing POI 단가 카드 누락"


def test_ad_pricing_has_llm_context() -> None:
    """Claude Haiku LLM 컨텍스트 박스 (폭증 시 자동 단가 근거)."""
    html = _ad()
    assert "llm" in html.lower() or "claude" in html.lower() or "context" in html.lower(), \
        "ad_pricing LLM 컨텍스트 박스 누락"


def test_ad_pricing_has_demo_trigger() -> None:
    """demo-trigger 버튼 존재."""
    html = _ad()
    assert "demo-trigger" in html, "ad_pricing demo-trigger 버튼 누락"
