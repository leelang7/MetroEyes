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
    """9개 핵심 검사 모두 CHECKS 리스트에 등록."""
    src = SCRIPT.read_text(encoding="utf-8")
    expected = [
        "check_required_files", "check_kpi_consistency", "check_dispersion_kpi",
        "check_pitch_figs_present", "check_4lang_parity", "check_ci_jobs_present",
        "check_changelog_recent", "check_python_imports", "check_pytest_pass",
    ]
    for fn in expected:
        assert f"def {fn}" in src, f"missing check function: {fn}"
        assert fn in src.split("CHECKS")[1] if "CHECKS" in src else False, \
            f"{fn} not in CHECKS list"


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

# NOTE: 실제 end-to-end 실행 (`python scripts/submission_check.py`)은 D-day 직전 수동 실행 권장.
# 이 도구가 내부적으로 pytest 를 다시 호출 → pytest 안에서 재귀 호출 시 timeout 발생하므로
# regression suite 에는 포함하지 않음. CI 별도 job 또는 사용자 수동 실행으로 검증.
