"""docs/RUNBOOK.md 장애 복구 docs 회귀 (cycle 376).

본선 발표 전 시연 장애 발생 시 1줄 복구 가능하도록 핵심 시나리오 9개 모두 명시.
공고문 평가지표 중 "운영 안정성"·"사고 대응" 정성 점수 어필.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RB = ROOT / "docs" / "RUNBOOK.md"


def _txt() -> str:
    return RB.read_text(encoding="utf-8")


def test_runbook_exists() -> None:
    assert RB.exists(), f"missing {RB}"


def test_9_scenarios_documented() -> None:
    """9 핵심 장애 시나리오 모두 섹션 헤더 존재."""
    t = _txt()
    needles = [
        "백엔드 죽음",
        "Cloudflare 터널 끊김",
        "GPS 안 잡힘",
        "LLM API 한도 초과",
        "WebSocket 끊김",
        "Demo fail-safe 8단",
        "KPI drift 자동 차단",
        "도메인 down",
        "체크리스트",
    ]
    for n in needles:
        assert n in t, f"runbook missing scenario: {n}"


def test_recovery_commands_present() -> None:
    """복구 1줄 명령 — start.bat / start_demo.ps1 / pytest / submission_check 명시."""
    t = _txt()
    assert "start.bat" in t, "start.bat 복구 명령 누락"
    assert "start_demo.ps1" in t, "start_demo.ps1 복구 명령 누락"
    assert "submission_check.py" in t, "submission_check.py D-day 명령 누락"
    assert "pytest" in t, "pytest 자가 검증 명령 누락"


def test_fail_safe_8_layers_documented() -> None:
    """8단 방어 메커니즘 표 — backend down 중에도 시연 유지."""
    t = _txt()
    for layer in ("--demo", "30초 incident injector", "5분 sticky bar",
                  "warm seed 12건", "Docker compose", "GitHub Actions CI"):
        assert layer in t, f"fail-safe layer missing: {layer}"


def test_pre_demo_checklist_documented() -> None:
    """발표 5분 전 체크리스트 — 4개 명령 모두 명시."""
    t = _txt()
    assert "/health" in t, "health check 명령 누락"
    assert "test_kpi_drift" in t, "KPI drift 검증 명령 누락"
    assert "submission_check" in t, "submission_check 명령 누락"


def test_contact_info_present() -> None:
    t = _txt()
    assert "leescvsir@gmail.com" in t, "developer email missing"
    assert "github.com/leelang7/MetroEyes" in t, "github repo URL missing"


def test_5second_grace_period_documented() -> None:
    """cycle 340 의 5초 offline grace + 30초 ping keepalive 명시."""
    t = _txt()
    assert "5초 offline grace" in t, "5초 grace period missing"
    assert "30초 ping" in t, "30s ping keepalive missing"
