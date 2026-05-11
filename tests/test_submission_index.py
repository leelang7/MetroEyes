"""docs/SUBMISSION_INDEX.md 평가 지표 ↔ 산출물 ↔ CI 가드 매핑 회귀 (cycle 381).

1차 서류 (개발 60 + 기획서 40 + 가점 5) + 2차 발표 (100점) 자기 채점표.
모든 청구의 근거가 산출물 파일 + CI 가드 ID + 정량 수치 cross-reference.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs" / "SUBMISSION_INDEX.md"


def _txt() -> str:
    return INDEX.read_text(encoding="utf-8")


def test_index_exists() -> None:
    assert INDEX.exists(), f"missing {INDEX}"


def test_1st_eval_sections_present() -> None:
    """1차 평가 (개발 60 / 기획서 40 / 가점 5) 모두 섹션."""
    t = _txt()
    for sec in ("개발 60점", "기획서 40점", "가점 5점", "1차 자기 채점"):
        assert sec in t, f"1차 평가 섹션 누락: {sec}"


def test_2nd_eval_categories_present() -> None:
    """2차 평가 6 카테고리 (공공데이터 25/AI 20/독창성 15/완성도 15/발전성 20/ESG 5)."""
    t = _txt()
    for cat in ("공공데이터 활용 (25점)", "AI 혁신성 (20점)", "독창성 (15점)",
                "완성도 (15점)", "발전 가능성 (20점)", "ESG (5점)"):
        assert cat in t, f"2차 평가 카테고리 누락: {cat}"


def test_self_score_205() -> None:
    """자기 채점 합계 205/205 (1차 105 + 2차 100)."""
    t = _txt()
    assert "205/205" in t, "총합 자기 채점 (205/205) 누락"
    assert "105/105" in t, "1차 자기 채점 (105/105) 누락"
    assert "100/100" in t, "2차 자기 채점 (100/100) 누락"


def test_critical_artifacts_referenced() -> None:
    """핵심 산출물 (PROPOSAL / SLIDES / pitch / onepager / RUNBOOK / QA) 모두 인덱스."""
    t = _txt()
    for f in ("docs/PROPOSAL.md", "docs/SLIDES.html", "docs/RUNBOOK.md",
              "docs/QA_PREPARATION.md", "docs/RECORDING_NARRATION.md",
              "frontend/pitch.html", "frontend/onepager.html", "frontend/demo.html"):
        assert f in t, f"인덱스에 핵심 산출물 누락: {f}"


def test_ci_guards_referenced() -> None:
    """주요 회귀 가드 ID 모두 cross-reference."""
    t = _txt()
    for g in ("test_kpi_drift", "test_runbook", "test_proposal_v3_alignment",
              "test_onepager", "test_evac_strengthen", "test_roi_ci_band"):
        assert g in t, f"인덱스에 가드 ID 누락: {g}"


def test_kpi_numbers_cross_referenced() -> None:
    """핵심 KPI (canonical 일치) 모두 인덱스 안에."""
    t = _txt()
    for kpi in ("1,393억", "347x", "708x", "320", "1,064~1,808"):
        assert kpi in t, f"인덱스에 KPI 누락: {kpi}"


def test_d_day_command_documented() -> None:
    """D-day 제출 직전 1줄 명령 명시."""
    t = _txt()
    assert "submission_check.py" in t, "submission_check 명령 누락"
    assert "--ci" in t, "--ci flag 명시 누락"
