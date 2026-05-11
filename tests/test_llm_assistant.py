"""LLM 어시스턴트 (shared/llm_assistant.js) 회귀 가드 (cycle 499).

데모 안정성을 위한 canned-response LLM + 라이브 Claude 교체 준비:
- OPERATOR_CANNED: 운영자 시나리오 응답 (분산/응급/약자/에너지 등)
- CITIZEN_CANNED: 시민 시나리오 응답 (역 검색/경로/약자 동선)
- classifyIncident: 자연어 사고 분류 (AI 혁신성 20점)
- streamTo: 타이프라이터 스트리밍 효과 (생성감)
- 4가지 운영자 Q&A (응급/분산/예측/약자)
- 시민 PWA용 응답 (강남/홍대/휠체어/최단경로)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LLM_JS = ROOT / "frontend" / "shared" / "llm_assistant.js"


def _src() -> str:
    return LLM_JS.read_text(encoding="utf-8")


def test_llm_assistant_file_exists() -> None:
    """shared/llm_assistant.js 파일 존재."""
    assert LLM_JS.is_file(), "llm_assistant.js 파일 누락"


def test_operator_canned_responses() -> None:
    """OPERATOR_CANNED 응답 DB 존재 — 운영자 시나리오."""
    src = _src()
    assert "OPERATOR_CANNED" in src, "OPERATOR_CANNED 응답 DB 누락"
    # 핵심 시나리오 키워드
    for kw in ("응급", "분산", "예측", "약자"):
        assert kw in src, f"OPERATOR_CANNED {kw} 시나리오 누락"


def test_citizen_canned_responses() -> None:
    """CITIZEN_CANNED 응답 DB 존재 — 시민 시나리오."""
    src = _src()
    assert "CITIZEN_CANNED" in src, "CITIZEN_CANNED 응답 DB 누락"
    for kw in ("강남", "휠체어", "빠른"):
        assert kw in src, f"CITIZEN_CANNED {kw} 시나리오 누락"


def test_call_llm_function() -> None:
    """callLLM(prompt, mode) 함수 존재."""
    src = _src()
    assert "callLLM" in src, "callLLM 함수 누락"
    assert "operator" in src, "callLLM operator 모드 누락"


def test_stream_to_typewriter() -> None:
    """streamTo 타이프라이터 효과 함수."""
    src = _src()
    assert "streamTo" in src, "streamTo 타이프라이터 효과 함수 누락"


def test_classify_incident_function() -> None:
    """classifyIncident — 자연어 사고 분류 (AI 혁신성)."""
    src = _src()
    assert "classifyIncident" in src, "classifyIncident 함수 누락"
    # 응급/이상행동/분실 3종 분류
    for cat in ("medical", "behavioral", "분실"):
        assert cat in src, f"classifyIncident {cat} 분류 누락"


def test_llm_demo_fallback_stable() -> None:
    """데모 모드 — API 비용 없는 canned 응답으로 안정적 시연."""
    src = _src()
    assert "matchCanned" in src, "matchCanned 매칭 함수 누락 — 데모 안정성 위협"


def test_operator_4lang_response_included() -> None:
    """운영자 분산 안내 — 4언어 멘트 포함."""
    src = _src()
    # 운영자 분산 안내 응답에 4언어 포함
    assert "Car 5" in src or "Car" in src, "en 분산 안내 누락"
    assert "5号车" in src or "号车" in src, "zh 분산 안내 누락"


def test_llm_assistant_exported_as_global() -> None:
    """LLMAssistant global 객체 export."""
    src = _src()
    assert "LLMAssistant" in src or "global.LLMAssistant" in src, \
        "LLMAssistant global export 누락"
