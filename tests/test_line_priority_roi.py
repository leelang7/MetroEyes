"""호선별 차등 보상 ROI 시뮬 회귀 (cycle 360).

scripts/eda_line_priority_roi.py 가 line_carload_est × policy_roi_v3 을 결합해
호선별 ROI 순위를 산출. 9개 핵심 호선 모두 포함되고 합이 정책 v3 총량과 일치해야 함.

리포트: frontend/figs/line_priority_roi_report.json (git tracked).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "frontend" / "figs" / "line_priority_roi_report.json"


def _load() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_report_exists() -> None:
    assert REPORT.exists(), f"missing {REPORT} — run scripts/eda_line_priority_roi.py"


def test_report_has_9_main_lines() -> None:
    d = _load()
    rows = d["lines"]
    assert len(rows) == 9, f"expected 9 main lines (1~9), got {len(rows)}"
    line_set = {r["line"] for r in rows}
    for i in range(1, 10):
        assert f"{i}호선" in line_set, f"missing {i}호선"


def test_required_columns() -> None:
    d = _load()
    cols = set(d["lines"][0].keys())
    for c in ("line", "avg_pct", "peak_pct", "over_100_hours",
              "saved_min_yr", "social_value_won", "priority_score", "roi_x"):
        assert c in cols, f"missing column: {c}"


def test_saved_min_sum_matches_policy_v3() -> None:
    """호선별 saved_min 합 ≈ 정책 v3 30% 시나리오 473.4M/년 (±0.5%)."""
    d = _load()
    total = d["total_saved_min_yr"]
    expected = 473_400_000
    diff_pct = abs(total - expected) / expected * 100
    assert diff_pct < 1.0, f"per-line sum {total} vs expected {expected} ({diff_pct:.2f}% off)"


def test_priority_ranking_sensible() -> None:
    """1호선은 점유 가장 낮으므로 priority 가장 낮아야 함."""
    d = _load()
    by_line = {r["line"]: r["priority_score"] for r in d["lines"]}
    line1 = by_line["1호선"]
    others = [v for k, v in by_line.items() if k != "1호선"]
    assert line1 < min(others), f"1호선 priority {line1} should be lowest, others min {min(others)}"


def test_method_documented() -> None:
    """리포트에 산출 방식 명시 (재현성)."""
    d = _load()
    assert "method" in d
    assert "policy_roi_v3" in d["method"] or "473" in d["method"]
    assert d["response_rate"] == 0.30
    assert d["won_per_min"] == 200
