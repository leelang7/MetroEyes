"""admin.html 호선×시간대 mini heatmap 회귀 (cycle 370).

cycle 368 의 line_hour_priority_matrix.json 을 admin.html 가 자동 fetch →
9×19 mini canvas heatmap 에 색상 + Top 5 cell 외곽선 + 텍스트 요약.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADMIN = ROOT / "frontend" / "admin.html"
REPORT = ROOT / "frontend" / "figs" / "line_hour_priority_matrix.json"


def _admin() -> str:
    return ADMIN.read_text(encoding="utf-8")


def test_canvas_dom_present() -> None:
    html = _admin()
    assert 'id="line-hour-canvas"' in html, "heatmap canvas missing"
    assert 'id="line-hour-top5"' in html, "top5 text summary missing"
    assert 'data-i18n="line_hour_h"' in html, "header data-i18n missing"


def test_loader_fetches_committed_report() -> None:
    html = _admin()
    assert "loadLineHourHeatmap" in html, "loader function missing"
    assert "fetch('figs/line_hour_priority_matrix.json'" in html, "report fetch missing"


def test_top5_outline_logic() -> None:
    """Top 5 cells 가 strokeRect 로 외곽 강조."""
    html = _admin()
    assert "j.top5_cells" in html, "top5_cells reference missing"
    assert "ctx.strokeRect" in html, "strokeRect for top5 outline missing"
    assert "#10b981" in html, "green outline color missing"


def test_color_gradient_thresholds() -> None:
    """0~160 점수 기준 cyan→orange→red 그라데이션."""
    html = _admin()
    # 주요 임계값 — 테스트가 너무 깐깐하지 않게 키워드만 확인
    assert "colorFor" in html, "colorFor function missing"
    assert "rgba(125, 211, 211" in html, "cyan tier color missing"
    assert "rgba(245, 158, 11" in html, "orange tier color missing"
    assert "rgba(255, 94, 87" in html, "red tier color missing"


def test_i18n_4lang_for_panel() -> None:
    html = _admin()
    for lang in ("ko", "en", "zh", "ja"):
        m = re.search(rf"\b{lang}: \{{(.*?)\}},", html, re.DOTALL)
        assert m, f"missing lang block {lang}"
        assert "line_hour_h:" in m.group(1), f"line_hour_h missing in {lang}"


def test_committed_report_still_present() -> None:
    """cycle 368 결과 JSON 이 admin 이 의존하는 경로에 그대로 있음."""
    assert REPORT.exists(), f"missing {REPORT} — cycle 368 결과 사라짐"
    d = json.loads(REPORT.read_text(encoding="utf-8"))
    assert "matrix" in d and len(d["matrix"]) == 9, "9 호선 매트릭스 필요"
    assert "top5_cells" in d and len(d["top5_cells"]) == 5, "top5 cell 5개 필요"
