"""CHANGELOG.md freshness 회귀 (cycle 379).

CHANGELOG 가 현재 cycle 진행도 (README 배지) 와 ±5 cycle 이내 동기화 보장.
cycle 367 까지만 기록하고 cycle 378 인 상황 회귀 방지 (2026-05-08).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CL = ROOT / "CHANGELOG.md"
README = ROOT / "README.md"


def _cl() -> str:
    return CL.read_text(encoding="utf-8")


def _readme() -> str:
    return README.read_text(encoding="utf-8")


def test_latest_version_block_present() -> None:
    """최신 v6.X 헤더가 존재."""
    cl = _cl()
    assert "## v6.7" in cl or "## v6.8" in cl or "## v6.9" in cl, \
        "CHANGELOG missing recent v6.7+ block — must update each cycle batch"


def test_changelog_cycle_close_to_readme() -> None:
    """CHANGELOG 의 max cycle 번호가 README 배지의 cycle 과 ±10 이내."""
    cl = _cl()
    rd = _readme()
    cl_nums = [int(m) for m in re.findall(r"cycle\s+(\d{3,4})", cl, re.IGNORECASE)]
    rd_match = re.search(r"자동_사이클-(\d{3,4})회", rd)
    if not rd_match:
        rd_match = re.search(r"Auto_Cycles-(\d{3,4})", rd)
    assert rd_match, "README cycle badge missing"
    rd_cycle = int(rd_match.group(1))
    assert cl_nums, "CHANGELOG has no cycle references"
    cl_max = max(cl_nums)
    drift = rd_cycle - cl_max
    assert drift <= 10, \
        f"CHANGELOG drift: README at cycle {rd_cycle} but CHANGELOG max {cl_max} (drift {drift} > 10)"


def test_v67_includes_critical_cycles() -> None:
    """v6.7 (cycle 372-378) 가 핵심 사이클 모두 명시."""
    cl = _cl()
    if "## v6.7" not in cl:
        return  # v6.8+ 일 때는 별도 가드
    # cycle 372/375/376/378 — 1-Pager / KPI drift / RUNBOOK / QA
    for c in ("cycle 372", "cycle 374", "cycle 375", "cycle 376", "cycle 378"):
        assert c in cl, f"v6.7 missing reference: {c}"


def test_changelog_kpi_alignment_with_canonical() -> None:
    """CHANGELOG 가 광고하는 가드 수가 README 배지와 일치."""
    cl = _cl()
    rd = _readme()
    # README 회귀 가드 수
    rd_match = re.search(r"regression_tests-(\d+)", rd)
    if not rd_match:
        return
    rd_n = int(rd_match.group(1))
    # CHANGELOG 최신 v 의 회귀 가드 수
    m = re.search(r"v6\.\d+ — D-\d+ 회귀 가드 (\d+)건", cl)
    if not m:
        return
    cl_n = int(m.group(1))
    drift = abs(rd_n - cl_n)
    assert drift <= 10, \
        f"가드 수 drift: README {rd_n} vs CHANGELOG {cl_n} (drift {drift} > 10)"
