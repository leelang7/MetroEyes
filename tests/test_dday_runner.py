"""scripts/dday.ps1 D-day 통합 검증 스크립트 회귀 (cycle 395).

사용자가 D-day (5/13) 직전 1줄 명령으로 모든 검증 실행 가능하도록 통합 runner 제공.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DDAY = ROOT / "scripts" / "dday.ps1"


def _txt() -> str:
    return DDAY.read_text(encoding="utf-8")


def test_dday_script_exists() -> None:
    assert DDAY.exists(), f"missing {DDAY}"


def test_three_modes_supported() -> None:
    """--full / --quick / --regen 3 모드 지원."""
    t = _txt()
    assert "Full" in t and "Quick" in t and "Regen" in t, "3 모드 param 누락"


def test_regen_runs_4_eda_scripts() -> None:
    """--regen 모드가 4 EDA 스크립트 재생성 (canonical KPI source of truth 갱신)."""
    t = _txt()
    assert "policy_roi_v3.py" in t, "policy_roi_v3 재생성 누락"
    assert "eda_line_priority_roi.py" in t, "line priority ROI 재생성 누락"
    assert "eda_line_hour_priority.py" in t, "line hour priority 재생성 누락"
    assert "eda_co2_savings.py" in t, "co2 savings 재생성 누락"


def test_pytest_step_present() -> None:
    """pytest 회귀 가드 모드 모두 실행."""
    t = _txt()
    assert "pytest tests/" in t, "pytest 단계 누락"
    assert "--ignore=tests/test_smoke.py" in t, "smoke 제외 옵션 누락"


def test_submission_check_step_present() -> None:
    """submission_check ship-gate 모드 모두 실행."""
    t = _txt()
    assert "submission_check.py" in t, "submission_check 단계 누락"
    assert "--ci" in t, "--ci 빠른 모드 분기 누락"


def test_outputs_color_coded() -> None:
    """결과 PASS/WARN/FAIL 색상 분기 (Green/Yellow/Red)."""
    t = _txt()
    assert "Green" in t, "PASS green color missing"
    assert "Yellow" in t, "WARN yellow color missing"
    assert "Red" in t, "FAIL red color missing"


def test_runbook_referenced_on_fail() -> None:
    """FAIL 시 RUNBOOK 9 시나리오 cross-link (cycle 376)."""
    t = _txt()
    assert "RUNBOOK" in t, "RUNBOOK reference missing"


# === cycle 412 — Mac/Linux dday.sh mirror ===

def test_dday_sh_mirror_exists() -> None:
    """Mac/Linux 사용자용 bash mirror — scripts/dday.sh."""
    sh = ROOT / "scripts" / "dday.sh"
    assert sh.exists(), f"missing {sh} — Mac/Linux dday mirror"
    body = sh.read_text(encoding="utf-8")
    # 4 EDA 스크립트 모두 호출
    for s in ("policy_roi_v3.py", "eda_line_priority_roi.py",
              "eda_line_hour_priority.py", "eda_co2_savings.py"):
        assert s in body, f"dday.sh missing EDA: {s}"
    # 3 모드 지원
    assert "--quick" in body and "--full" in body and "--regen" in body, \
        "dday.sh missing 3 mode support"
    # submission_check + pytest
    assert "submission_check.py" in body and "pytest" in body
    # bash shebang
    assert body.startswith("#!/usr/bin/env bash"), "bash shebang missing"


# === cycle 419 — Makefile (3rd platform parity) ===

def test_makefile_exists() -> None:
    """Makefile (third-platform parity for dday.ps1/sh)."""
    mk = ROOT / "Makefile"
    assert mk.exists(), f"missing {mk}"
    body = mk.read_text(encoding="utf-8")
    # 6 targets 모두
    for target in ("verify:", "full:", "regen:", "test:", "demo:", "clean:"):
        assert target in body, f"Makefile missing target: {target}"
    # 4 EDA scripts in full/regen
    for s in ("policy_roi_v3.py", "eda_line_priority_roi.py",
              "eda_line_hour_priority.py", "eda_co2_savings.py"):
        assert s in body, f"Makefile missing EDA: {s}"
    # cross-platform reference
    assert "dday.ps1" in body or "dday.sh" in body, \
        "Makefile missing cross-platform reference"
