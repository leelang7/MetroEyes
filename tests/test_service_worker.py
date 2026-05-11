"""passenger_app/sw.js 서비스 워커 회귀 가드 (cycle 511).

IDEA-9 도착 알림 + PWA 오프라인 캐싱:
- CACHE 키 + ASSETS 배열 (index.html/onboard.html/styles.css/shared JS)
- install: caches.addAll + skipWaiting
- activate: 오래된 캐시 삭제 + clients.claim
- fetch: cache-first 전략
- notificationclick: metroeyes-arrival 태그 + PWA 포커스/오픈
- message 이벤트: metroeyes-arrival 위임 → showNotification
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SW_JS = ROOT / "frontend" / "passenger_app" / "sw.js"


def _src() -> str:
    return SW_JS.read_text(encoding="utf-8")


def test_service_worker_exists() -> None:
    """passenger_app/sw.js 존재."""
    assert SW_JS.is_file(), "sw.js 서비스 워커 누락"


def test_sw_cache_key_defined() -> None:
    """CACHE 상수 정의."""
    src = _src()
    assert "const CACHE" in src or "CACHE =" in src, "CACHE 상수 누락"


def test_sw_assets_include_core_files() -> None:
    """ASSETS 배열 — index.html/onboard.html/styles.css/manifest.webmanifest."""
    src = _src()
    for asset in ("index.html", "onboard.html", "styles.css", "manifest.webmanifest"):
        assert asset in src, f"ASSETS {asset} 누락"


def test_sw_assets_include_shared_js() -> None:
    """ASSETS — 공유 JS (bev_engine/safety_features/llm_assistant)."""
    src = _src()
    for js in ("bev_engine.js", "safety_features.js", "llm_assistant.js"):
        assert js in src, f"ASSETS shared/{js} 누락"


def test_sw_install_skip_waiting() -> None:
    """install 핸들러 — skipWaiting 즉시 활성화."""
    src = _src()
    assert "install" in src, "install 이벤트 핸들러 누락"
    assert "skipWaiting" in src, "skipWaiting 누락"


def test_sw_activate_clients_claim() -> None:
    """activate 핸들러 — clients.claim + 구 캐시 삭제."""
    src = _src()
    assert "activate" in src, "activate 이벤트 핸들러 누락"
    assert "clients.claim" in src, "clients.claim 누락"
    assert "caches.delete" in src, "구 캐시 삭제 누락"


def test_sw_fetch_cache_first() -> None:
    """fetch 핸들러 — caches.match 캐시 우선."""
    src = _src()
    assert "fetch" in src, "fetch 이벤트 핸들러 누락"
    assert "caches.match" in src, "caches.match 캐시 우선 전략 누락"


def test_sw_notification_click_handler() -> None:
    """notificationclick — metroeyes-arrival 태그 처리."""
    src = _src()
    assert "notificationclick" in src, "notificationclick 핸들러 누락"
    assert "metroeyes-arrival" in src, "metroeyes-arrival 알림 태그 누락"


def test_sw_notification_pwa_focus() -> None:
    """notificationclick — PWA 클라이언트 포커스/오픈."""
    src = _src()
    assert "c.focus" in src or "client.focus" in src, "PWA 포커스 동작 누락"
    assert "openWindow" in src, "openWindow 새 창 오픈 누락"


def test_sw_message_show_notification() -> None:
    """message 이벤트 — metroeyes-arrival 위임 → showNotification."""
    src = _src()
    assert "message" in src, "message 이벤트 핸들러 누락"
    assert "showNotification" in src, "showNotification 위임 누락"
    assert "renotify" in src, "renotify 설정 누락"
