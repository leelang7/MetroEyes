"""frontend/shared/health_pill.js 회귀 가드 (cycle 541 — WS readyState 기반).

운영자 4페이지 공용 백엔드 상태 pill:
- POLL_MS 폴링 간격
- ensurePill: DOM 동적 생성 + header 자동 삽입
- window.LIVE_WS / window.ws / window._ws readyState 체크
- 2단계 상태: 🟢연결됨 / ⚫끊김
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PILL_JS = ROOT / "frontend" / "shared" / "health_pill.js"


def _src() -> str:
    return PILL_JS.read_text(encoding="utf-8")


def test_health_pill_exists() -> None:
    """shared/health_pill.js 존재."""
    assert PILL_JS.is_file(), "health_pill.js 누락"


def test_health_pill_poll_interval() -> None:
    """POLL_MS 폴링 상수 존재."""
    src = _src()
    assert "POLL_MS" in src, "POLL_MS 상수 누락"
    assert "setInterval" in src, "setInterval 폴링 누락"


def test_health_pill_ensure_pill_function() -> None:
    """ensurePill 함수 — DOM element 동적 생성."""
    src = _src()
    assert "ensurePill" in src, "ensurePill 함수 누락"
    assert "health-pill" in src or "PILL_ID" in src, "health-pill element ID 누락"


def test_health_pill_ws_reference() -> None:
    """window.LIVE_WS / window.ws / window._ws readyState 체크."""
    src = _src()
    assert "LIVE_WS" in src, "LIVE_WS 참조 누락"
    assert "readyState" in src, "readyState 체크 누락"


def test_health_pill_2_states() -> None:
    """2단계 상태 배지 — 🟢 연결됨 / ⚫ 끊김."""
    src = _src()
    assert "🟢" in src, "🟢 연결됨 상태 누락"
    assert "⚫" in src, "⚫ 끊김 상태 누락"


def test_health_pill_offline_badge() -> None:
    """⚫ 끊김 오프라인 배지."""
    src = _src()
    assert "⚫" in src, "⚫ 오프라인 배지 누락"
    assert "끊김" in src, "끊김 메시지 누락"


def test_health_pill_connected_text() -> None:
    """연결됨 텍스트 표시."""
    src = _src()
    assert "연결됨" in src, "연결됨 메시지 누락"


def test_health_pill_setinterval_poll() -> None:
    """setInterval(poll, POLL_MS) — 주기적 폴링."""
    src = _src()
    assert "setInterval" in src, "setInterval 폴링 호출 누락"
    assert "poll" in src, "poll 함수 호출 누락"
