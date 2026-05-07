"""admin.html 호선별 ROI 라이브 추천 패널 회귀 (cycle 366).

cycle 360 의 line_priority_roi_report.json 을 admin.html 가 자동 fetch 해서
🥇/🥈/🥉 메달 ranked list 로 즉시 노출. 운영자에게 "지금 어느 호선에 우선" 답.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADMIN = ROOT / "frontend" / "admin.html"
REPORT = ROOT / "frontend" / "figs" / "line_priority_roi_report.json"


def _admin() -> str:
    return ADMIN.read_text(encoding="utf-8")


def test_panel_dom_present() -> None:
    """🎯 호선별 추천 패널 DOM 요소 존재."""
    html = _admin()
    for el_id in ("line-roi-rank", "line-roi-meta"):
        assert f'id="{el_id}"' in html, f"missing element id: {el_id}"


def test_panel_loads_committed_report() -> None:
    """admin.html 가 frontend/figs/line_priority_roi_report.json fetch 호출."""
    html = _admin()
    assert "fetch('figs/line_priority_roi_report.json'" in html, "report fetch missing"
    # 정렬 + 메달 + 2호선 강조
    assert "priority_score" in html
    assert "L.line === '2호선'" in html, "2호선 special highlight missing"
    for medal in ("🥇", "🥈", "🥉"):
        assert medal in html, f"missing medal: {medal}"


def test_i18n_4lang_for_panel_header() -> None:
    """line_roi_h 키가 4언어 모두 정의."""
    html = _admin()
    for lang in ("ko", "en", "zh", "ja"):
        m = re.search(rf"\b{lang}: \{{(.*?)\}},", html, re.DOTALL)
        assert m, f"missing lang block {lang}"
        assert "line_roi_h:" in m.group(1), f"line_roi_h missing in {lang}"


def test_committed_report_still_present() -> None:
    """cycle 360 결과 JSON 이 admin 이 의존하는 경로에 그대로 있음."""
    assert REPORT.exists(), f"missing {REPORT} — cycle 360 결과 사라짐"
    d = json.loads(REPORT.read_text(encoding="utf-8"))
    assert len(d.get("lines", [])) == 9, "9호선 모두 있어야 admin 패널 정상"


def test_panel_safe_fail_on_static_host() -> None:
    """fetch 실패 시 (정적 호스팅) catch 로 조용히 종료."""
    html = _admin()
    # try/catch wrapping the panel loader
    assert "loadLineRoi" in html, "loader function missing"
    assert "} catch (e)" in html or "} catch {" in html, "fetch catch handler missing"
