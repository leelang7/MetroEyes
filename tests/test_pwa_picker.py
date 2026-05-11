"""시민 PWA 역 picker 강화 회귀 (cycle 359).

기존 picker (검색창 + GPS 정렬) 에 호선 필터 chips + 9호선/신분당선 stations 추가.

장애 시나리오: chip 핸들러 누락 / 추가된 station 누락 / SW cache 버전 미갱신.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PWA = ROOT / "frontend" / "passenger_app" / "index.html"
SW = ROOT / "frontend" / "passenger_app" / "sw.js"


def _pwa() -> str:
    return PWA.read_text(encoding="utf-8")


def _sw() -> str:
    return SW.read_text(encoding="utf-8")


def test_line_filter_chips_dom_present() -> None:
    html = _pwa()
    assert 'id="modal-line-chips"' in html, "line filter chips container missing"
    for line_id in ('"all"', '"1"', '"2"', '"5"', '"9"', '"bonus"'):
        assert f'data-line={line_id}' in html, f"missing line chip: {line_id}"


def test_line_filter_state_var() -> None:
    html = _pwa()
    assert "_lineFilter" in html, "line filter state var missing"
    assert "if (_lineFilter && _lineFilter !== 'all')" in html, "filter logic missing"


def test_bonus_filter_uses_od_or_transfer() -> None:
    """💰 보너스 chip 은 OD/환승 station 만 노출."""
    html = _pwa()
    assert "_lineFilter === 'bonus'" in html, "bonus filter branch missing"
    assert "s.od || s.transfer" in html, "bonus filter predicate missing"


def test_new_stations_added() -> None:
    """9호선/신분당선/강남업무지구 핵심 station — shared/seoul_stations.js 로 이동."""
    from pathlib import Path
    sta_js = (Path(__file__).resolve().parent.parent
              / "frontend" / "shared" / "seoul_stations.js").read_text(encoding="utf-8")
    # shared 파일에 있어야 하고, pwa는 SEOUL_STATIONS 참조해야 함
    html = _pwa()
    assert "SEOUL_STATIONS" in html, "SEOUL_STATIONS 참조 누락 in pwa"
    for name in ("신논현", "고속터미널", "잠실새내", "용산", "신논현"):
        assert name in sta_js, f"missing station in seoul_stations.js: {name}"


def test_sw_cache_version_bumped() -> None:
    """SW cache 버전 v8 (이전 v7-a11y) — 시민 폰에 picker 즉시 반영."""
    sw = _sw()
    assert "subwaybev-citizen-v8-stationpicker" in sw, "SW cache version not bumped to v8"


def test_chip_click_handler_wired() -> None:
    html = _pwa()
    assert ".line-chip" in html, "line-chip class selector missing"
    assert "addEventListener('click'" in html, "chip click handler missing"
    assert "renderModalList" in html, "renderModalList re-trigger missing"
