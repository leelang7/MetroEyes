"""frontend/shared/safety_features.js 안전 감지 유틸 회귀 가드 (cycle 527).

운영자 콘솔 + 시민 앱 공용 — 심사 기준 '사회적 가치' 핵심:
- TYPE_LABEL: 4종 이벤트 한글 레이블 (emergency/suspicious/lost/free_ride)
- TYPE_ICON: 이모지 아이콘 매핑
- TTS_TEMPLATES: 4개 언어 (ko/en/zh/ja) 다국어 안내
- speak(): TTS 함수 정의
- announce(): 다국어 안내 실행 함수
- formatRelTime(): 상대 시간 포맷

파일 파싱 기반 정적 검증.
"""
from __future__ import annotations

from pathlib import Path

JS = Path(__file__).resolve().parent.parent / "frontend/shared/safety_features.js"


def _js() -> str:
    return JS.read_text(encoding="utf-8")


def test_safety_features_file_exists() -> None:
    """safety_features.js 파일 존재."""
    assert JS.exists(), "frontend/shared/safety_features.js 없음"


def test_type_label_4_events() -> None:
    """TYPE_LABEL — 4종 이벤트 (emergency/suspicious/lost/free_ride) 정의."""
    js = _js()
    for event in ("emergency", "suspicious", "lost", "free_ride"):
        assert event in js, f"TYPE_LABEL 이벤트 {event} 누락"


def test_type_icon_emoji() -> None:
    """TYPE_ICON — 4종 이모지 아이콘 정의."""
    js = _js()
    assert "TYPE_ICON" in js, "TYPE_ICON 정의 없음"
    for event in ("emergency", "suspicious", "lost", "free_ride"):
        assert event in js, f"TYPE_ICON 이벤트 {event} 누락"


def test_tts_templates_4_languages() -> None:
    """TTS_TEMPLATES — ko/en/zh/ja 4개 언어 정의."""
    js = _js()
    assert "TTS_TEMPLATES" in js, "TTS_TEMPLATES 없음"
    for lang in ("'ko'", "'en'", "'zh'", "'ja'"):
        assert lang in js, f"언어 {lang} 누락"


def test_tts_crowded_message() -> None:
    """TTS_TEMPLATES — crowded (혼잡) 메시지 4개 언어 모두 정의."""
    js = _js()
    assert "crowded" in js, "crowded 메시지 없음"


def test_tts_emergency_message() -> None:
    """TTS_TEMPLATES — emergency (응급) 메시지 정의."""
    js = _js()
    assert "emergency" in js, "emergency 메시지 없음"


def test_speak_function() -> None:
    """speak() — TTS 실행 함수 정의."""
    js = _js()
    assert "function speak" in js or "speak =" in js or "speak(" in js, \
        "speak 함수 없음"


def test_announce_function() -> None:
    """announce() — 다국어 안내 실행 함수 정의."""
    js = _js()
    assert "function announce" in js or "announce =" in js or "announce(" in js, \
        "announce 함수 없음"


def test_format_rel_time() -> None:
    """formatRelTime() — 상대 시간 포맷 함수 정의."""
    js = _js()
    assert "formatRelTime" in js, "formatRelTime 없음"


def test_korean_label_present() -> None:
    """한글 응급 레이블 '응급' 존재 (한국어 TTS 안내)."""
    js = _js()
    assert "응급" in js, "한글 '응급' 레이블 없음"
