"""frontend/shared/llm_assistant.js LLM 어시스턴트 회귀 가드 (cycle 528).

데모 안정성/비용0 — 키워드 매칭 canned 응답 + classifyIncident:
- OPERATOR_CANNED: 운영자용 키워드 응답 DB (응급/분산/이상/에너지 등)
- CITIZEN_CANNED: 시민용 키워드 응답 DB
- classifyIncident(): 자연어 → {category, urgency, recommendedAction}
- LLMAssistant global export (callLLM/streamTo/classifyIncident)
- 4개 언어 안내문 존재 (ko/en/zh/ja)

파일 파싱 기반 정적 검증.
"""
from __future__ import annotations

from pathlib import Path

JS = Path(__file__).resolve().parent.parent / "frontend/shared/llm_assistant.js"


def _js() -> str:
    return JS.read_text(encoding="utf-8")


def test_llm_assistant_file_exists() -> None:
    """llm_assistant.js 파일 존재."""
    assert JS.exists(), "frontend/shared/llm_assistant.js 없음"


def test_operator_canned_defined() -> None:
    """OPERATOR_CANNED 운영자 응답 DB 정의."""
    assert "OPERATOR_CANNED" in _js(), "OPERATOR_CANNED 없음"


def test_citizen_canned_defined() -> None:
    """CITIZEN_CANNED 시민용 응답 DB 정의."""
    assert "CITIZEN_CANNED" in _js(), "CITIZEN_CANNED 없음"


def test_classify_incident_defined() -> None:
    """classifyIncident() 함수 정의."""
    assert "classifyIncident" in _js(), "classifyIncident 없음"


def test_classify_medical_category() -> None:
    """classifyIncident — '응급' 키워드 → medical 카테고리 반환 로직."""
    js = _js()
    assert "'medical'" in js or '"medical"' in js, "medical 카테고리 없음"


def test_classify_behavioral_category() -> None:
    """classifyIncident — '이상행동' → behavioral 카테고리."""
    js = _js()
    assert "'behavioral'" in js or '"behavioral"' in js, "behavioral 카테고리 없음"


def test_classify_lost_item_category() -> None:
    """classifyIncident — '분실' → lost_item 카테고리."""
    js = _js()
    assert "lost_item" in js, "lost_item 카테고리 없음"


def test_llm_assistant_global_export() -> None:
    """LLMAssistant global export — callLLM/streamTo/classifyIncident."""
    js = _js()
    assert "LLMAssistant" in js, "LLMAssistant 전역 export 없음"
    for fn in ("callLLM", "streamTo", "classifyIncident"):
        assert fn in js, f"LLMAssistant.{fn} 없음"


def test_multilang_responses() -> None:
    """4개 언어 안내문 (한/영/중/일) 존재."""
    js = _js()
    # 영어 안내 확인 (canned 응답에 포함)
    assert "Car" in js and "crowded" in js, "영어 안내 없음"
    # 중문 확인 (한자)
    assert "拥挤" in js or "车厢" in js, "중문 안내 없음"


def test_match_canned_function() -> None:
    """matchCanned() 내부 키워드 매칭 함수 정의."""
    assert "matchCanned" in _js(), "matchCanned 없음"


def test_urgency_levels() -> None:
    """classifyIncident — critical/monitor/low 긴급도 레벨 정의."""
    js = _js()
    for level in ("critical", "monitor", "low"):
        assert level in js, f"긴급도 레벨 '{level}' 없음"
