"""docs/ + frontend/ outdated CI/가드 텍스트 자동 차단 (cycle 384).

cycle 318-331 / CI 10 jobs / 30 가드 같은 outdated 마커가 PROPOSAL / SLIDES /
INNOVATION_TRIZ / pitch.html 안에 남아있어 심사위원에게 stale 인상 주는 회귀 방지.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 검사 대상 파일 (모두 광고 자료)
FILES = [
    "docs/PROPOSAL.md",
    "docs/SLIDES.html",
    "docs/SLIDES_DECK.md",
    "docs/INNOVATION_TRIZ.md",
    "frontend/pitch.html",
]


def _read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def test_no_outdated_ci_jobs_30_guards() -> None:
    """광고 자료에서 'CI 10 jobs + 30 가드' 등 outdated 표기 제거."""
    bad_patterns = [
        "CI 10 jobs + pytest 회귀 가드 30건",
        "CI 10 jobs + 30 pytest 회귀 가드",
        "CI 12 jobs + 41 회귀 가드",
        "CI 12 jobs/41 회귀 가드",
        "CI 12 jobs/41 가드",
    ]
    failures = []
    for f in FILES:
        body = _read(f)
        for bad in bad_patterns:
            if bad in body:
                failures.append(f"{f} contains outdated: '{bad}'")
    assert not failures, "outdated CI/가드 표기 발견:\n  " + "\n  ".join(failures)


def test_no_outdated_cycle_318_331_336() -> None:
    """광고 자료에서 'cycle 318-331' 같은 outdated cycle 범위 표기 제거."""
    bad_patterns = ["cycle 318-331", "cycle 318-336"]
    failures = []
    for f in FILES:
        body = _read(f)
        for bad in bad_patterns:
            if bad in body:
                failures.append(f"{f} contains outdated cycle range: '{bad}'")
    assert not failures, "outdated cycle 범위 표기 발견:\n  " + "\n  ".join(failures)


def test_recent_ci_count_advertised_in_proposal() -> None:
    """PROPOSAL §16 (또는 본문) 에 CI 14+ jobs / 가드 150+ 광고."""
    p = _read("docs/PROPOSAL.md")
    m_jobs = re.search(r"CI\s+(\d+)\s+jobs", p)
    m_guards = re.search(r"(\d+)\s*회귀\s*가드", p)
    if m_jobs:
        assert int(m_jobs.group(1)) >= 14, f"PROPOSAL CI {m_jobs.group(1)} jobs too old"
    if m_guards:
        assert int(m_guards.group(1)) >= 150, f"PROPOSAL {m_guards.group(1)} 가드 too old"


def test_canonical_kpi_drift_mentioned() -> None:
    """주요 자료에 canonical KPI drift 자동 차단 (cycle 375) 명시."""
    found_count = 0
    for f in FILES:
        body = _read(f)
        if "canonical" in body.lower() or "drift" in body.lower():
            found_count += 1
    assert found_count >= 2, f"canonical KPI drift 명시 자료 부족: {found_count} (≥2 필요)"
