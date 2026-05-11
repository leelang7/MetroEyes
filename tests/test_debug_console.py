"""frontend/admin.html 디버그 콘솔 회귀 가드 (cycle 512).

MetroEyes Debug Console (루트 admin.html — operator_web/admin.html 과 별개):
- MetroEyes Debug Console 브랜드
- WS 직접 호출 / 응답 검증 / 라이브 트래픽 / 임팩트 모니터링
- 4언어 토글 (lang-toggle)
- WebSocket URL 설정 + 연결 상태 LED
- 수동 제어 버튼 (arrival_query / population_query 등)
- health 폴링 + 임팩트 요약 패널
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADMIN_ROOT = ROOT / "frontend" / "admin.html"


def _html() -> str:
    return ADMIN_ROOT.read_text(encoding="utf-8")


def test_debug_console_exists() -> None:
    """frontend/admin.html 존재 (operator_web/admin.html 과 별개 파일)."""
    assert ADMIN_ROOT.is_file(), "frontend/admin.html 디버그 콘솔 누락"


def test_debug_console_brand() -> None:
    """MetroEyes Debug Console 브랜드."""
    html = _html()
    assert "MetroEyes" in html, "MetroEyes 브랜드 누락"
    assert "Debug Console" in html or "debug" in html.lower(), "Debug Console 식별자 누락"


def test_debug_console_lang_toggle() -> None:
    """lang-toggle 버튼 존재."""
    html = _html()
    assert "lang-toggle" in html, "lang-toggle 버튼 누락"


def test_debug_console_ws_led() -> None:
    """WebSocket 연결 상태 LED (ws-led)."""
    html = _html()
    assert "ws-led" in html, "WebSocket 상태 LED 누락"


def test_debug_console_websocket_url_input() -> None:
    """WebSocket URL 입력 / URL bar."""
    html = _html()
    assert "url-bar" in html or "ws" in html.lower(), "WebSocket URL 설정 누락"


def test_debug_console_arrival_query() -> None:
    """arrival_query 컨트롤 — 실시간 도착 조회."""
    html = _html()
    assert "arrival" in html.lower() or "arrival_query" in html, "arrival_query 컨트롤 누락"


def test_debug_console_population_query() -> None:
    """population_query 컨트롤 — 인구/혼잡도 조회."""
    html = _html()
    assert "population" in html.lower() or "citydata" in html.lower(), "인구 조회 컨트롤 누락"


def test_debug_console_impact_panel() -> None:
    """임팩트 모니터링 패널."""
    html = _html()
    assert "impact" in html.lower() or "임팩트" in html, "임팩트 모니터링 패널 누락"


def test_debug_console_tokens_css() -> None:
    """shared/tokens.css 참조."""
    html = _html()
    assert "tokens.css" in html, "shared/tokens.css 참조 누락"
