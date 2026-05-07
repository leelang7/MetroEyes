"""GitHub PR/Issue templates + CONTRIBUTING.md 회귀 (cycle 385).

리포 첫 방문 / 협업 인상이 평가에 미치는 영향 — 평가위원이 GitHub 직접 browse 시
PR 양식 / Issue 양식 / CONTRIBUTING 모두 갖춘 mature project 표시.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_pr_template_exists() -> None:
    p = ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
    assert p.exists(), f"missing {p}"
    body = p.read_text(encoding="utf-8")
    assert "회귀 가드" in body, "PR template missing regression guard checklist"
    assert "submission_check" in body, "PR template missing submission_check command"
    assert "canonical" in body.lower(), "PR template missing canonical KPI reference"


def test_bug_report_template_exists() -> None:
    p = ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.md"
    assert p.exists(), f"missing {p}"
    body = p.read_text(encoding="utf-8")
    assert "재현 절차" in body, "bug template missing reproduction steps"
    assert "RUNBOOK" in body, "bug template missing RUNBOOK cross-ref"


def test_feature_request_template_exists() -> None:
    p = ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.md"
    assert p.exists(), f"missing {p}"
    body = p.read_text(encoding="utf-8")
    assert "사용자 가치" in body, "feature template missing user value rationale"
    assert "회귀 가드" in body, "feature template missing regression guard plan"


def test_contributing_md_exists() -> None:
    p = ROOT / "CONTRIBUTING.md"
    assert p.exists(), f"missing {p}"
    body = p.read_text(encoding="utf-8")
    assert "submission_check" in body, "CONTRIBUTING missing submission_check"
    assert "RUNBOOK" in body and "QA_PREPARATION" in body, "CONTRIBUTING missing key docs cross-ref"
    assert "Apache 2.0" in body, "CONTRIBUTING missing license"


def test_contributing_links_to_canonical() -> None:
    """CONTRIBUTING 가 canonical KPI workflow 명시 (cycle 374 회귀 회피)."""
    p = ROOT / "CONTRIBUTING.md"
    body = p.read_text(encoding="utf-8")
    assert "canonical" in body.lower() and "kpi" in body.lower(), "CONTRIBUTING missing canonical KPI section"
    assert "policy_roi_v3.py" in body, "CONTRIBUTING missing canonical regen command"
    assert "test_kpi_drift" in body, "CONTRIBUTING missing drift test reference"
