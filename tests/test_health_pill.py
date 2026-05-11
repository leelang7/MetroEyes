"""frontend/shared/health_pill.js 회귀 가드 (cycle 510).

운영자 4페이지 공용 백엔드 상태 pill:
- POLL_MS=8000 폴링 간격
- ensurePill: DOM 동적 생성 + header 자동 삽입
- deriveHealthURL: LIVE_WS_URL / wss: / ws: 자동 전환
- poll: CV fps + API 오류율 + WebSocket 클라이언트 수 배지
- 3단계 상태: 🟢OK / 🟡부분 / 🔴점검
- 끊김 시 ⚫ 오프라인 배지
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
    """POLL_MS = 8000 (8초 폴링)."""
    src = _src()
    assert "POLL_MS" in src, "POLL_MS 상수 누락"
    assert "8000" in src, "8초 폴링 간격 누락"


def test_health_pill_ensure_pill_function() -> None:
    """ensurePill 함수 — DOM element 동적 생성."""
    src = _src()
    assert "ensurePill" in src, "ensurePill 함수 누락"
    assert "health-pill" in src or "PILL_ID" in src, "health-pill element ID 누락"


def test_health_pill_derive_health_url() -> None:
    """deriveHealthURL — LIVE_WS_URL + wss:/ws: 전환."""
    src = _src()
    assert "deriveHealthURL" in src, "deriveHealthURL 함수 누락"
    assert "LIVE_WS_URL" in src, "LIVE_WS_URL 참조 누락"
    assert "wss://" in src or "wss:" in src, "WSS 프로토콜 전환 누락"


def test_health_pill_3_states() -> None:
    """3단계 상태 배지 — 🟢 / 🟡 / 🔴."""
    src = _src()
    assert "🟢" in src, "🟢 OK 상태 누락"
    assert "🟡" in src, "🟡 부분 가용 상태 누락"
    assert "🔴" in src, "🔴 점검 필요 상태 누락"


def test_health_pill_offline_badge() -> None:
    """백엔드 끊김 시 ⚫ 오프라인 배지."""
    src = _src()
    assert "⚫" in src, "⚫ 오프라인 배지 누락"
    assert "백엔드 끊김" in src or "backend" in src.lower(), "끊김 메시지 누락"


def test_health_pill_cv_fps_display() -> None:
    """CV fps 표시 — cv.fps."""
    src = _src()
    assert "cv.fps" in src or "fps" in src, "CV fps 표시 누락"


def test_health_pill_setinterval_poll() -> None:
    """setInterval(poll, POLL_MS) — 주기적 폴링."""
    src = _src()
    assert "setInterval" in src, "setInterval 폴링 호출 누락"
    assert "poll" in src, "poll 함수 호출 누락"
