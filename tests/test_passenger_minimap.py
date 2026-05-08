"""3D OpenFreeMap mini-map 회귀 가드 (cycle 425).

시민 PWA 의 GPS 자동 매칭에 추가된 MapLibre GL JS 기반 3D 지도 위젯:
- OpenFreeMap liberty style (3D building extrusion)
- 사용자 GPS 도트 + 33개 역 marker + nearest highlight + dest polyline
- 외부 CDN 로드 실패 시 fallback (텍스트 거리 표시 유지)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PWA = ROOT / "frontend" / "passenger_app" / "index.html"


def _txt() -> str:
    return PWA.read_text(encoding="utf-8")


def test_maplibre_cdn_loaded() -> None:
    """MapLibre GL JS CSS + JS CDN 둘 다 로드."""
    t = _txt()
    assert "maplibre-gl@4" in t, "MapLibre GL JS pinned version 누락"
    assert "maplibre-gl.css" in t, "MapLibre CSS 누락"
    assert "maplibre-gl.js" in t, "MapLibre JS 누락"


def test_openfreemap_style_url() -> None:
    """OpenFreeMap liberty style url (3D buildings 지원)."""
    t = _txt()
    assert "tiles.openfreemap.org/styles/liberty" in t, \
        "OpenFreeMap liberty style url 누락 — 3D buildings 안 나옴"


def test_minimap_dom_container() -> None:
    """#mini-map div + #mini-map-card wrapper 존재."""
    t = _txt()
    assert 'id="mini-map-card"' in t, "#mini-map-card wrapper 누락"
    assert 'id="mini-map"' in t, "#mini-map container div 누락"
    assert 'id="mm-recenter"' in t, "재중심 버튼 누락"


def test_minimap_3d_building_extrusion() -> None:
    """3D building extrusion layer 추가 (fill-extrusion type)."""
    t = _txt()
    assert "fill-extrusion" in t, "3D building extrusion layer 누락"
    assert "mm-3d-buildings" in t, "3D building layer id 누락"
    assert "pitch:" in t.lower() or "pitch:" in t, "3D 시점 pitch 설정 누락"


def test_minimap_user_gps_marker() -> None:
    """사용자 GPS 도트 marker (mm-marker-user)."""
    t = _txt()
    assert "mm-marker-user" in t, "사용자 GPS marker 클래스 누락"
    assert "_mmUserMarker" in t, "사용자 marker 변수 누락"


def test_minimap_station_markers() -> None:
    """33개 역 marker + nearest highlight."""
    t = _txt()
    assert "mm-marker-station" in t, "역 marker 클래스 누락"
    assert ".nearest" in t, "nearest 강조 클래스 누락"
    assert "_mmStationMarkers" in t, "역 marker 배열 누락"


def test_minimap_dest_polyline() -> None:
    """도착지 marker + 사용자→도착지 polyline."""
    t = _txt()
    assert "setMiniMapDest" in t, "setMiniMapDest 함수 누락"
    assert "mm-route" in t, "route polyline source 누락"
    assert "mm-marker-station dest" in t or "dest" in t, "도착지 marker 클래스 누락"


def test_minimap_fallback_on_cdn_fail() -> None:
    """CDN 로드 실패 시 fallback 카드 hide."""
    t = _txt()
    assert "_markMmFailed" in t, "fallback 함수 누락"
    assert "mini-map-fallback" in t, "fallback 메시지 컨테이너 누락"
    assert "card.classList.add('failed')" in t or '"failed"' in t, \
        "fallback CSS class 트리거 누락"


def test_minimap_wired_into_gps_flow() -> None:
    """GPS getCurrentPosition success 콜백이 updateMiniMap 호출."""
    t = _txt()
    assert "updateMiniMap(pos.coords.latitude, pos.coords.longitude" in t, \
        "GPS 성공 시 updateMiniMap 호출 누락"


def test_minimap_wired_into_setdestination() -> None:
    """setDestination + clearDestination 둘 다 mini-map sync."""
    t = _txt()
    # setDestination 안에서 _setMiniMapDest(s) 호출
    assert "window._setMiniMapDest(s)" in t, \
        "setDestination -> _setMiniMapDest(s) wiring 누락"
    # clearDestination 안에서 _setMiniMapDest(null)
    assert "window._setMiniMapDest(null)" in t, \
        "clearDestination -> _setMiniMapDest(null) wiring 누락"
