"""호선 × 시간대 우선순위 매트릭스 회귀 (cycle 368).

cycle 360 의 line-only ranking 을 line × hour 2D 매트릭스로 확장.
"어느 호선 어느 시간대" 정확한 정책 표적 답.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "frontend" / "figs" / "line_hour_priority_matrix.json"


def _load() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_report_exists() -> None:
    assert REPORT.exists(), f"missing {REPORT} — run scripts/eda_line_hour_priority.py"


def test_9_lines_19_hours() -> None:
    """9 호선 × 19 시간 (5~23시) 매트릭스 형상."""
    d = _load()
    assert len(d["lines"]) == 9, f"expected 9 main lines, got {len(d['lines'])}"
    assert d["hours"] == list(range(5, 24)), "hours must be 5..23"
    for r in d["matrix"]:
        # 19 hours per line
        assert len(r["hours"]) == 19, f"line {r['line']} hour cells != 19"


def test_top5_cells_have_score() -> None:
    """Top 5 cells 모두 line/hour/score 가지며 internal-consistent."""
    d = _load()
    top5 = d["top5_cells"]
    assert len(top5) == 5
    last_score = float("inf")
    for c in top5:
        assert "line" in c and "hour" in c and "score" in c
        assert c["line"] in d["lines"], f"unknown line in top5: {c['line']}"
        assert c["hour"] in d["hours"], f"unknown hour in top5: {c['hour']}"
        assert c["score"] <= last_score, "top5 must be score-descending"
        last_score = c["score"]


def test_2hosun_dominant_in_peak() -> None:
    """2호선 9/17/19시 가 Top 5 안에 — cycle 360 의 1순위 호선과 일치."""
    d = _load()
    top5 = d["top5_cells"]
    has_2_peak = any(c["line"] == "2호선" and c["hour"] in (8, 9, 17, 18, 19) for c in top5)
    assert has_2_peak, f"2호선 peak hours expected in Top 5, got {top5}"


def test_1hosun_lowest_at_5am() -> None:
    """1호선 5시 가 Bottom 5 (점유 가장 낮음)."""
    d = _load()
    bottom5 = d["bottom5_cells"]
    has_1_5am = any(c["line"] == "1호선" and c["hour"] == 5 for c in bottom5)
    assert has_1_5am, f"1호선 5시 expected in Bottom 5, got {bottom5}"


def test_bias_applied_correctly() -> None:
    """commute_response_bias 가 출근 0.7 / 퇴근 1.0 으로 적용됨."""
    d = _load()
    bias = d["bias_table"]
    assert bias["8"] == 0.7, f"8시 bias = 0.7, got {bias['8']}"
    assert bias["18"] == 1.0, f"18시 bias = 1.0, got {bias['18']}"
    # 9시/17시/19시 모두 1.05 (자율도 ↑)
    assert bias["9"] == 1.05 and bias["17"] == 1.05 and bias["19"] == 1.05


def test_method_documented() -> None:
    d = _load()
    assert "occ_pct" in d["method"]
    assert "commute_response_bias" in d["method"]
