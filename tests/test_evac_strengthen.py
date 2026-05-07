"""realbev.html 비상 동선 알고리즘 강화 회귀 (cycle 358).

기존 A*+Hungarian 1:1 매칭에 4가지 강화 기능 추가:
1. 출구 차단 토글 (NW/NE/SW/SE 개별 on/off)
2. 그룹 수 ≠ 출구 수 시 그리디 폴백 매칭
3. ETA 초 변환 (그리드 셀 0.5m, 보행 1.4 m/s)
4. 4분면 단순 baseline 비교 (단일 출구 절감률 + 4분면 절감률 동시 표시)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REALBEV = ROOT / "frontend" / "operator_web" / "realbev.html"


def _html() -> str:
    return REALBEV.read_text(encoding="utf-8")


def test_exit_blockage_ui_present() -> None:
    """4개 출구 개별 차단 토글 버튼 존재."""
    html = _html()
    for exit_id in ("NW", "NE", "SW", "SE"):
        assert f'data-exit="{exit_id}"' in html, f"missing exit blockage button: {exit_id}"
    assert "exit-block-btn" in html, "exit-block-btn class missing"
    assert "_blockedExits" in html, "blocked exits state missing"


def test_eta_seconds_conversion() -> None:
    """ETA 초 변환 — 그리드 셀 0.5m, 보행 1.4 m/s."""
    html = _html()
    assert "GRID_CELL_M = 0.5" in html, "grid cell size constant missing"
    assert "WALK_SPEED_MS = 1.4" in html, "walking speed constant missing"
    assert "stepsToSec" in html, "steps-to-seconds converter missing"
    assert "ETA " in html, "ETA label missing in result render"


def test_quadrant_baseline_comparison() -> None:
    """4분면 단순 baseline 절감률 표시 (Hungarian 효용 정량화)."""
    html = _html()
    assert "quadrantCost" in html, "quadrant baseline cost var missing"
    assert "vsQuadPct" in html, "quadrant savings pct missing"
    # 단일 출구 baseline 도 유지
    assert "singleExitCost" in html, "single-exit baseline must remain"
    assert "distributedSavePct" in html, "distributed save pct must remain"


def test_greedy_fallback_when_exits_blocked() -> None:
    """출구 차단으로 그룹 수 ≠ 출구 수 시 그리디 매칭 폴백."""
    html = _html()
    assert "groups.length === exits.length" in html, "exact-match condition missing"
    # 그룹 > 출구 시 fallback (중복 출구 허용)
    assert "groups.map((_, g) =>" in html or "matching = groups.map" in html, "greedy fallback missing"


def test_blocked_exit_indicator_in_result() -> None:
    """결과 표시에 '차단 N/4' 표시 (운영자가 즉시 인지)."""
    html = _html()
    assert "_blockedExits.size" in html, "blocked count check missing"
    assert "blockedNote" in html, "blocked note rendering missing"
