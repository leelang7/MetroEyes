"""shared/ 공유 엔진 (bev_engine.js / safety_features.js) 회귀 가드 (cycle 500).

공유 엔진은 지하철·버스 운영자·시민 앱 모두에서 재사용:
- bev_engine.js: BEV 시뮬레이션 + 승객 물리엔진 (BoT-SORT 모방)
- safety_features.js: 사고 알림 TTS + 접근성 모드 + toast

두 엔진 모두 production-grade 재사용 설계 — M4 진입장벽 근거.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BEV_JS = ROOT / "frontend" / "shared" / "bev_engine.js"
SAFETY_JS = ROOT / "frontend" / "shared" / "safety_features.js"


def _bev() -> str:
    return BEV_JS.read_text(encoding="utf-8")


def _safety() -> str:
    return SAFETY_JS.read_text(encoding="utf-8")


# ── bev_engine.js ──

def test_bev_engine_exists() -> None:
    """shared/bev_engine.js 존재."""
    assert BEV_JS.is_file(), "bev_engine.js 누락"


def test_bev_engine_create_sim() -> None:
    """createSim 팩토리 함수 — 지하철/버스 시뮬 생성."""
    src = _bev()
    assert "createSim" in src, "createSim 함수 누락"


def test_bev_engine_passenger_physics() -> None:
    """승객 물리엔진 — steerToward + separate (BoT-SORT 모방)."""
    src = _bev()
    assert "steerToward" in src, "steerToward 함수 누락"
    assert "separate" in src, "separate 충돌 회피 함수 누락"


def test_bev_engine_draw_person() -> None:
    """drawPerson — BEV canvas 렌더링 함수."""
    src = _bev()
    assert "drawPerson" in src, "drawPerson 렌더링 함수 누락"


def test_bev_engine_lost_item_detection() -> None:
    """drawLostItem — 분실물 자동 감지 렌더링."""
    src = _bev()
    assert "drawLostItem" in src, "drawLostItem 분실물 감지 렌더링 누락"


def test_bev_engine_incident_emitter() -> None:
    """emitIncident — 사고 이벤트 발신 (운영자 콘솔 동기화)."""
    src = _bev()
    assert "emitIncident" in src, "emitIncident 사고 이벤트 발신 누락"


def test_bev_engine_door_zones() -> None:
    """doorsByRole + nearestDoorByRole — 문 zone 병목 감지."""
    src = _bev()
    assert "doorsByRole" in src, "doorsByRole 함수 누락"


def test_bev_engine_exported_as_global() -> None:
    """BEVEngine global 객체 export."""
    src = _bev()
    assert "BEVEngine" in src or "global.BEVEngine" in src, "BEVEngine global export 누락"


# ── safety_features.js ──

def test_safety_features_exists() -> None:
    """shared/safety_features.js 존재."""
    assert SAFETY_JS.is_file(), "safety_features.js 누락"


def test_safety_features_announce() -> None:
    """announce(kind, lang, params) — 4언어 TTS 안내."""
    src = _safety()
    assert "announce" in src, "announce 함수 누락"


def test_safety_features_speak() -> None:
    """speak(text, langCode) — SpeechSynthesis 래퍼."""
    src = _safety()
    assert "speak" in src, "speak 함수 누락"
    assert "speechSynthesis" in src or "SpeechSynthesis" in src, \
        "SpeechSynthesis 호출 누락"


def test_safety_features_push_toast() -> None:
    """pushToast — 사고 알림 toast 스택 UI."""
    src = _safety()
    assert "pushToast" in src, "pushToast 함수 누락"


def test_safety_features_accessibility_mode() -> None:
    """applyAccessibilityMode — 시각 약자/고령층 접근성 모드."""
    src = _safety()
    assert "applyAccessibilityMode" in src or "accessibility" in src.lower(), \
        "접근성 모드 함수 누락"


def test_safety_features_exported_as_global() -> None:
    """SafetyFeatures global 객체 export."""
    src = _safety()
    assert "SafetyFeatures" in src, "SafetyFeatures global export 누락"
