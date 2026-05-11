"""mobile_app/lib/main.dart Flutter 앱 엔트리포인트 회귀 가드 (cycle 532).

MetroEyes 시민 앱 핵심:
- StationCoord: 12개 주요 역 (GPS 매칭용)
- _haversineKm(): Haversine 거리 공식 (GPS → 최근접 역)
- _nearestStation(): 최근접 역 탐색
- 디자인 토큰: _accent = #7DD3D3 (MetroEyes 브랜드 teal)
- MetroEyesApp runApp 엔트리포인트

파일 파싱 기반 정적 검증.
"""
from __future__ import annotations

from pathlib import Path

DART = Path(__file__).resolve().parent.parent / "mobile_app/lib/main.dart"


def _dart() -> str:
    return DART.read_text(encoding="utf-8")


def test_flutter_main_exists() -> None:
    """mobile_app/lib/main.dart 파일 존재."""
    assert DART.exists(), "mobile_app/lib/main.dart 없음"


def test_metroeyes_app_class() -> None:
    """MetroEyesApp — runApp 엔트리포인트."""
    d = _dart()
    assert "MetroEyesApp" in d, "MetroEyesApp 없음"
    assert "runApp" in d, "runApp 없음"


def test_station_coord_class() -> None:
    """StationCoord — GPS 매칭용 역 데이터 클래스."""
    d = _dart()
    assert "class StationCoord" in d, "StationCoord 없음"
    for field in ("name", "line", "lat", "lon"):
        assert field in d, f"StationCoord.{field} 없음"


def test_stations_list_12() -> None:
    """_stations — 12개 주요 역 정의 (시연/GPS 매칭용)."""
    d = _dart()
    # 대표적 역 존재 확인
    for station in ("잠실", "강남", "홍대입구", "서울역"):
        assert station in d, f"역 '{station}' 누락"


def test_haversine_formula() -> None:
    """_haversineKm() — 지구 반경 6371km Haversine 공식."""
    d = _dart()
    assert "haversine" in d.lower() or "_haversineKm" in d, "Haversine 함수 없음"
    assert "6371" in d, "지구 반경 6371 상수 없음"


def test_nearest_station_function() -> None:
    """_nearestStation() — 최근접 역 탐색."""
    d = _dart()
    assert "_nearestStation" in d, "_nearestStation 없음"


def test_accent_color_teal() -> None:
    """_accent = 0xFF7DD3D3 (MetroEyes 브랜드 teal)."""
    d = _dart()
    assert "7DD3D3" in d.upper() or "7dd3d3" in d, "_accent teal 없음"


def test_population_poi_field() -> None:
    """StationCoord.populationPoi — 서울 실시간 도시데이터 POI 매핑."""
    d = _dart()
    assert "populationPoi" in d, "populationPoi 없음"


def test_bev_socket_import() -> None:
    """main.dart — bev_socket.dart 임포트."""
    assert "bev_socket" in _dart(), "bev_socket import 없음"
