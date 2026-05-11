"""docs/QA_PREPARATION.md 2차 발표 Q&A 준비 회귀 (cycle 378).

본선 평가 (7/6) Q&A 5~10분 — 18개 예상 질문 5 카테고리 + 30초 self-pitch.
모든 답변이 데이터 근거 + CI 가드 ID cross-reference 보유.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QA = ROOT / "docs" / "QA_PREPARATION.md"


def _txt() -> str:
    return QA.read_text(encoding="utf-8")


def test_qa_exists() -> None:
    assert QA.exists(), f"missing {QA}"


def test_18_questions_documented() -> None:
    """Q1~Q18 모든 질문 헤더 존재."""
    t = _txt()
    for i in range(1, 19):
        assert f"### Q{i}." in t, f"missing Q{i} header"


def test_5_categories_present() -> None:
    """5 카테고리 — 통계 / 기술 / 사업화 / 윤리 / 발표 전략."""
    t = _txt()
    for cat in ("통계 / 정량 검증", "기술 / 구현 가능성", "사업화 / 시장성",
                "윤리 / 법 / 사회", "발표 흐름 / 전략"):
        assert cat in t, f"missing category: {cat}"


def test_critical_kpi_cross_referenced() -> None:
    """모든 핵심 KPI 가 답변 안에 cross-reference."""
    t = _txt()
    for kpi in ("1,393억", "347x", "708x", "157M", "1,064", "1,808"):
        assert kpi in t, f"missing KPI in QA: {kpi}"


def test_ci_guard_files_referenced() -> None:
    """답변마다 회귀 가드 파일 명시 — 답변 신뢰도 ↑."""
    t = _txt()
    needed_refs = [
        "test_kpi_drift.py", "test_roi_ci_band.py", "test_eda_dispersion.py",
        "test_openapi_spec.py", "test_runbook.py", "test_demo_orchestration.py",
    ]
    for f in needed_refs:
        assert f in t, f"missing test guard reference: {f}"


def test_self_pitch_30sec_present() -> None:
    """모든 질문 끝에 가능한 30초 self-pitch 명시."""
    t = _txt()
    assert "self-pitch" in t.lower() or "self_pitch" in t.lower(), "self-pitch section missing"
    assert re.search(r"\b[123]\d{2}\b", t), "current guard count (100+) must be in self-pitch"


def test_avoid_phrases_documented() -> None:
    """답변 회피 표현 — '잘 모르겠습니다' 대안 명시."""
    t = _txt()
    assert "잘 모르겠습니다" in t, "회피 표현 example missing"
    assert "❌" in t, "avoid markers missing"


def test_cross_reference_table_present() -> None:
    """답변 시 즉시 보일 화면 cross-reference 표."""
    t = _txt()
    assert "cross-reference" in t.lower() or "cross reference" in t.lower(), "cross-ref table missing"
    # 표 안에 핵심 페이지 명시
    for page in ("admin.html", "pitch.html", "onepager.html", "RUNBOOK"):
        assert page in t, f"missing screen reference: {page}"
