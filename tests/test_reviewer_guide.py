"""README "For Reviewers" 섹션 회귀 (cycle 382).

평가위원이 README 처음 보고 5분 안에 핵심 자료 (onepager / demo / pitch / index / QA)
순서대로 navigate 가능하도록 보장.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README_KO = ROOT / "README.md"
README_EN = ROOT / "README.en.md"


def _ko() -> str:
    return README_KO.read_text(encoding="utf-8")


def _en() -> str:
    return README_EN.read_text(encoding="utf-8")


def test_for_reviewers_section_present() -> None:
    """평가위원 / For Reviewers 섹션 양 README 모두 존재."""
    assert "평가위원" in _ko() or "For Reviewers" in _ko(), "ko README missing reviewers section"
    assert "For Reviewers" in _en(), "en README missing reviewers section"


def test_5_priority_artifacts_linked() -> None:
    """우선순위 5 자료 (onepager / demo / pitch / SUBMISSION_INDEX / QA) 모두 링크."""
    ko = _ko()
    for f in ("frontend/onepager.html", "frontend/demo.html", "frontend/pitch.html",
              "docs/SUBMISSION_INDEX.md", "docs/QA_PREPARATION.md"):
        assert f in ko, f"ko README missing reviewer artifact: {f}"
    en = _en()
    for f in ("frontend/onepager.html", "frontend/demo.html", "frontend/pitch.html",
              "docs/SUBMISSION_INDEX.md", "docs/QA_PREPARATION.md"):
        assert f in en, f"en README missing reviewer artifact: {f}"


def test_tldr_summary_present() -> None:
    """짧은 요약 (TL;DR) — 핵심 KPI 즉답 가능."""
    ko = _ko()
    en = _en()
    # ko 짧은 요약
    assert "1,393억" in ko and "708x" in ko, "ko TL;DR missing core KPI"
    # 가드 카운트 (drift 자동 감지 가능 — 정확 매치 불필요, 3자리 숫자 등장 보장)
    import re
    assert re.search(r"\b\d{3}\s*회귀\s*가드", ko) or re.search(r"\b\d{3}\s+가드", ko), \
        "ko TL;DR missing guard count"
    # en TL;DR
    assert "139.3B" in en and "708x" in en, "en TL;DR missing core KPI"
    assert re.search(r"\b\d{3}\s+regression\s+guards", en), "en TL;DR missing guard count"


def test_runbook_proposal_referenced() -> None:
    """추가 docs (RUNBOOK + PROPOSAL) 모두 reviewers 안내 안에 링크."""
    ko = _ko()
    en = _en()
    for f in ("docs/RUNBOOK.md", "docs/PROPOSAL.md"):
        assert f in ko, f"ko README missing additional doc: {f}"
        assert f in en, f"en README missing additional doc: {f}"


def test_priority_order_documented() -> None:
    """우선순위 1~5 명시 (number 명시)."""
    ko = _ko()
    en = _en()
    # 우선순위 표에서 1, 2, 3, 4, 5 마크 (또는 동등)
    assert "**1**" in ko and "**5**" in ko, "ko 5-priority order missing"
    assert "**1**" in en and "**5**" in en, "en 5-priority order missing"
