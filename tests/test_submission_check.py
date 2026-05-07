"""scripts/submission_check.py 자체 회귀 (cycle 367).

D-5 마감 직전 한 번에 검증하는 도구가 늘 통과하는지 자동화.
manifest 가 표류하지 않도록 핵심 검사 9개가 모두 등록되어 있는지 보장.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "submission_check.py"


def test_script_exists() -> None:
    assert SCRIPT.exists(), f"missing {SCRIPT}"


def test_script_compiles() -> None:
    """py_compile — 구문 오류 즉시 차단 (dataclass importlib 충돌 회피)."""
    r = subprocess.run([sys.executable, "-m", "py_compile", str(SCRIPT)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
    assert r.returncode == 0, f"compile failed: {r.stderr}"


def test_all_checks_registered() -> None:
    """9개 핵심 검사 모두 FAST_CHECKS + HEAVY_CHECKS 리스트에 등록 (cycle 380)."""
    src = SCRIPT.read_text(encoding="utf-8")
    expected_fast = [
        "check_required_files", "check_kpi_consistency", "check_dispersion_kpi",
        "check_pitch_figs_present", "check_4lang_parity", "check_ci_jobs_present",
        "check_changelog_recent",
    ]
    expected_heavy = ["check_python_imports", "check_pytest_pass"]
    # 함수 정의 모두 존재
    for fn in expected_fast + expected_heavy:
        assert f"def {fn}" in src, f"missing check function: {fn}"
    # FAST_CHECKS 와 HEAVY_CHECKS 분류
    fast_block = src.split("FAST_CHECKS")[1].split("HEAVY_CHECKS")[0] if "FAST_CHECKS" in src else ""
    heavy_block = src.split("HEAVY_CHECKS")[1].split("CHECKS:")[0] if "HEAVY_CHECKS" in src else ""
    for fn in expected_fast:
        assert fn in fast_block, f"{fn} not in FAST_CHECKS"
    for fn in expected_heavy:
        assert fn in heavy_block, f"{fn} not in HEAVY_CHECKS"


def test_exit_codes_documented() -> None:
    """0=PASS / 1=WARN / 2=FAIL — 외부 자동화에서 의존하는 종료 코드."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "return 0" in src and "return 1" in src and "return 2" in src, \
        "exit code 0/1/2 분기 누락"


def test_help_text_present() -> None:
    """모듈 docstring + 사용법 라인 보존 (D-5 마감 시각 명시)."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "D-5" in src or "마감" in src, "마감 명시 docstring 누락"
    assert "submission_check" in src, "스크립트 명 self-reference 누락"
    assert "pre-submission" in src.lower() or "제출" in src, "사용 목적 docstring 누락"


# === cycle 380 — --ci mode ===

def test_ci_mode_flag_supported() -> None:
    """--ci 플래그로 fast 모드 진입 (heavy import / pytest 제외)."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert '"--ci" in args' in src, "--ci CLI flag 처리 누락"
    assert "FAST_CHECKS" in src, "FAST_CHECKS 분류 누락"
    assert "HEAVY_CHECKS" in src, "HEAVY_CHECKS 분류 누락"


def test_ci_mode_runs_passes() -> None:
    """--ci 모드 현재 시점에서 PASS (exit 0)."""
    r = subprocess.run([sys.executable, str(SCRIPT), "--ci"],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=30)
    assert r.returncode == 0, (
        f"submission_check --ci FAIL/WARN — 회귀 발생\n"
        f"stdout tail:\n{r.stdout[-1200:]}"
    )


# === cycle 388 — required_files 확장 ===

def test_extended_required_files_includes_new_docs() -> None:
    """submission_check 의 required_files 가 cycle 367-386 신규 docs 모두 포함."""
    src = SCRIPT.read_text(encoding="utf-8")
    new_required = [
        "docs/RUNBOOK.md", "docs/QA_PREPARATION.md", "docs/SUBMISSION_INDEX.md",
        "docs/RECORDING_NARRATION.md",
        "frontend/onepager.html",
        "CONTRIBUTING.md", "SECURITY.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        "frontend/figs/policy_roi_v3_canonical_kpi.json",
        "frontend/figs/policy_roi_v3_ci_band.json",
        "frontend/figs/line_priority_roi_report.json",
        "frontend/figs/line_hour_priority_matrix.json",
        "scripts/eda_line_hour_priority.py",
        "scripts/submission_check.py",
    ]
    for f in new_required:
        assert f in src, f"submission_check required_files missing: {f}"


def test_canonical_kpi_json_referenced() -> None:
    """canonical KPI source of truth (cycle 375) 가 required 안에 명시."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "policy_roi_v3_canonical_kpi.json" in src, "canonical KPI JSON not in required_files"
    assert "policy_roi_v3_ci_band.json" in src, "CI band JSON not in required_files"

# NOTE: 실제 end-to-end 실행 (`python scripts/submission_check.py`)은 D-day 직전 수동 실행 권장.
# 이 도구가 내부적으로 pytest 를 다시 호출 → pytest 안에서 재귀 호출 시 timeout 발생하므로
# regression suite 에는 포함하지 않음. CI 별도 job 또는 사용자 수동 실행으로 검증.
