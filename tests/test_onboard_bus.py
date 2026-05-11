"""passenger_app/onboard.html 버스 탑승 중 UX 회귀 가드 (cycle 500).

버스 탑승 중 시민 경험:
- 4언어 실시간 도착 알림 (TTS: ko/en/zh/ja)
- ETA 카운트다운 (도착 N분 전)
- 차내 점유율 실시간 표시
- 외국인 환영 toast (navigator.language 자동 감지)
- 분산 인센티브 적립 표시
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ONBOARD = ROOT / "frontend" / "passenger_app" / "onboard.html"


def _html() -> str:
    return ONBOARD.read_text(encoding="utf-8")


def test_onboard_exists() -> None:
    """passenger_app/onboard.html 존재."""
    assert ONBOARD.is_file(), "onboard.html 버스 탑승 페이지 누락"


def test_onboard_metroeyes_brand() -> None:
    """MetroEyes 브랜드 표시."""
    html = _html()
    assert "MetroEyes" in html, "MetroEyes 브랜드 누락"


def test_onboard_4lang_toggle() -> None:
    """언어 토글 — navigator.language 자동 감지 + 수동 전환."""
    html = _html()
    assert "lang" in html.lower(), "언어 설정 누락"
    assert "navigator.language" in html, "navigator.language 자동 감지 누락"


def test_onboard_tts_4lang() -> None:
    """SpeechSynthesis 4언어 도착 알림."""
    html = _html()
    assert "speechSynthesis" in html or "SpeechSynthesis" in html, \
        "SpeechSynthesis TTS 누락"
    # 4언어 TTS 언어 코드
    for code in ("ko-KR", "en-US", "zh-CN", "ja-JP"):
        assert code in html, f"TTS 언어 코드 {code} 누락"


def test_onboard_eta_countdown() -> None:
    """ETA 카운트다운 — 도착 N분 전 표시."""
    html = _html()
    assert "ETA" in html or "eta" in html.lower() or "도착" in html, \
        "ETA 카운트다운 누락"


def test_onboard_welcome_toast_4lang() -> None:
    """외국인 환영 toast — 4언어 자동."""
    html = _html()
    assert "Welcome" in html or "welcome" in html.lower() or "환영" in html, \
        "외국인 환영 toast 누락"
    assert "navigator.language" in html, "언어 자동 감지 누락"


def test_onboard_incentive_display() -> None:
    """분산 인센티브 적립 표시."""
    html = _html()
    assert "krw" in html.lower() or "원" in html or "incentive" in html.lower() or "적립" in html, \
        "분산 인센티브 적립 표시 누락"


def test_manifest_webmanifest_exists() -> None:
    """PWA 설치를 위한 manifest.webmanifest 존재."""
    manifest = ROOT / "frontend" / "passenger_app" / "manifest.webmanifest"
    assert manifest.is_file(), "manifest.webmanifest 누락"


def test_manifest_pwa_required_fields() -> None:
    """manifest.webmanifest 필수 필드: name, start_url, display, icons."""
    import json
    manifest = ROOT / "frontend" / "passenger_app" / "manifest.webmanifest"
    if not manifest.is_file():
        return
    data = json.loads(manifest.read_text(encoding="utf-8"))
    for field in ("name", "start_url", "display", "icons"):
        assert field in data, f"manifest.webmanifest {field} 필드 누락"
    assert data["display"] == "standalone", "PWA standalone 모드 설정 필요"
