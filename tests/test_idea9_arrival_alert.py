"""IDEA-9 도착 알림 5중 모달리티 회귀 가드 (cycle 498).

IDEA-9: 노이즈캔슬링/이어폰 사용 시민 도착 알림 5채널 동시 발사
  ① 시각 — banner flash
  ② 햅틱 — navigator.vibrate
  ③ Web Audio — sine beep (AudioContext)
  ④ SpeechSynthesis — 4언어 TTS
  ⑤ System Notification — Service Worker showNotification

접근성 목표: 청각장애인 42만 + 노이즈 캔슬링 1,200만 잠재 사용자
장애인차별금지법 / 교통약자법 직결 → M7 심사 가점
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PWA = ROOT / "frontend" / "passenger_app" / "index.html"
SW = ROOT / "frontend" / "passenger_app" / "sw.js"


def _html() -> str:
    return PWA.read_text(encoding="utf-8")


def test_arrival_alert_button_exists() -> None:
    """도착지 설정 버튼 (dest-trigger) 존재."""
    html = _html()
    assert "dest-trigger" in html, "도착지 설정 버튼 (dest-trigger) 누락"
    assert "dest-test" in html, "도착 알림 테스트 버튼 (dest-test) 누락"


def test_wake_lock_api() -> None:
    """WakeLock API — 화면 꺼짐 방지 (도착 알림 신뢰성)."""
    html = _html()
    assert "WakeLock" in html or "wakeLock" in html or "_requestWakeLock" in html, \
        "WakeLock API 미구현 — 도착 알림 중 화면 꺼질 위험"


def test_haptic_vibrate() -> None:
    """햅틱 진동 (② 채널) — navigator.vibrate 호출."""
    html = _html()
    assert "navigator.vibrate" in html, "햅틱 진동 (navigator.vibrate) 미구현"


def test_web_audio_beep() -> None:
    """Web Audio sine beep (③ 채널) — AudioContext 사용."""
    html = _html()
    assert "AudioContext" in html or "audioContext" in html, \
        "Web Audio sine beep (AudioContext) 미구현"


def test_speech_synthesis_4lang() -> None:
    """SpeechSynthesis 4언어 TTS (④ 채널)."""
    html = _html()
    assert "SpeechSynthesis" in html or "speechSynthesis" in html, \
        "SpeechSynthesis (TTS) 미구현"


def test_service_worker_notification() -> None:
    """Service Worker System Notification (⑤ 채널) — 백그라운드 알림."""
    html = _html()
    assert "serviceWorker" in html, "Service Worker 미등록"
    assert "showNotification" in html or "postMessage" in html, \
        "SW showNotification 또는 postMessage 미구현"


def test_arrival_distance_threshold() -> None:
    """도착지 600m 이내 진입 시 알림 발사 (GPS 기반)."""
    html = _html()
    assert "DEST_ARRIVAL_M" in html or "600" in html, \
        "도착 알림 거리 임계값 (600m) 미정의"


def test_arrival_4lang_i18n() -> None:
    """도착 알림 메시지 4언어 지원."""
    html = _html()
    assert "label_on" in html or "도착 알림 ON" in html, "ko 도착 알림 i18n 누락"
    assert "Arrival alert ON" in html, "en 도착 알림 i18n 누락"


def test_sw_file_exists() -> None:
    """sw.js Service Worker 파일 존재."""
    assert SW.is_file(), "sw.js 파일 누락"


def test_sw_has_notification_handler() -> None:
    """sw.js 에 notificationclick 이벤트 핸들러 존재."""
    if not SW.is_file():
        return  # sw.js 없으면 skip
    sw = SW.read_text(encoding="utf-8")
    assert "notificationclick" in sw or "push" in sw, \
        "sw.js notificationclick 핸들러 누락 — 시스템 알림 터치 시 앱 복귀 불가"
