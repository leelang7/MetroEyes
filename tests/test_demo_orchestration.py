"""demo.html 5분 통합 시연 회귀 (cycle 363).

cycle 356/358/360 의 신규 핵심 기능들이 SCRIPT 에 명시적으로 등장해야 발표 영상에서 노출됨.

장애 시나리오: 신규 overlay 함수 누락 / SCRIPT timestamp 빠짐 / 종료 시각 5분 미만.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "frontend" / "demo.html"


def _html() -> str:
    return DEMO.read_text(encoding="utf-8")


def test_new_overlay_functions_defined() -> None:
    """cycle 356/358/360 신규 overlay 함수 3개 모두 정의."""
    html = _html()
    for fn in ("showAiPricingOverlay", "showEvacOverlay", "showLineRoiOverlay"):
        assert f"function {fn}(" in html, f"missing demo overlay: {fn}"


def test_new_overlay_branding() -> None:
    """각 overlay 의 핵심 키워드 (심사위원에게 어필할 수치/모델명)."""
    html = _html()
    # cycle 356 — Claude Haiku
    assert "Claude Haiku" in html, "AI pricing overlay must reference Claude Haiku"
    # cycle 358 — Hungarian + ETA
    assert "Hungarian" in html, "evac overlay must mention Hungarian"
    assert "1.4 m/s" in html or "1.4 m" in html or "보행 1.4" in html, "evac ETA formula missing"
    # cycle 360 (cycle 374 alignment) — 2호선 ROI 708x · 157M분
    assert "708x" in html, "line ROI overlay must show 2호선 708x (cycle 374 v3 alignment)"
    assert "157M" in html, "line ROI must reference 157M saved (광고 일치)"
    assert "₩400M" in html or "400M" in html, "line ROI budget reference missing"


def test_script_includes_new_stages() -> None:
    """SCRIPT timestamps 에 신규 3 stage 모두 등장 (cycle 356/358/360)."""
    html = _html()
    # cycle 363 에서 추가한 새 timestamp 들 — 광고 LLM (10s), A* (150s), 호선 ROI (240s)
    assert "showAiPricingOverlay" in html, "AI pricing stage not in SCRIPT"
    assert "showEvacOverlay" in html, "evac stage not in SCRIPT"
    assert "showLineRoiOverlay" in html, "line ROI stage not in SCRIPT"
    # 신규 stage 텍스트
    for kw in ("cycle 356", "cycle 358", "cycle 360"):
        assert kw in html, f"missing cycle reference in SCRIPT: {kw}"


def test_total_duration_5min() -> None:
    """total duration 5*60*1000 = 300000ms 유지."""
    html = _html()
    assert "5 * 60 * 1000" in html or "5*60*1000" in html, "5-minute timer logic missing"
    # 마지막 stage timestamp 가 275s 까지 (5분 시연 종료 직전)
    assert "[275000," in html, "last stage at 275s missing — extends to 5-min end"


def test_no_orphan_old_timestamps() -> None:
    """기존 248000ms 종료가 275000ms 로 이동했는지 (cycle 363 작업 검증)."""
    html = _html()
    # 248000 (4분 8초) old timestamp 가 SCRIPT 안 끝 stage 로 더 이상 등장하지 않음
    matches = re.findall(r"\[248000,", html)
    assert len(matches) == 0, f"orphan old [248000,...] timestamp still in SCRIPT: {matches}"
