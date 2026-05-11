"""mobile_app/lib/bev_socket.dart BevSocket Dart 회귀 가드 (cycle 533).

MetroEyes Flutter 앱 WebSocket 통신 레이어:
- BevPayload: fps/frameIdx/tracks, personCount/vehicleCount/personPerBin()
- SocketState enum: disconnected/connecting/connected/error
- ArrivalRow: etaSeconds getter (arvlCd=5→0)
- PopulationResponse: ppltnMid getter
- ImpactSummary: totalCount/avgSavedPct
- BevSocket WS 메시지 타입: arrival_query/population_query/citydata_query/events_query/impact_log/phone_telemetry/citizen_report
- citizenReport: source='flutter-app'
- ngrok 무료 tier 우회 헤더

파일 파싱 기반 정적 검증.
"""
from __future__ import annotations

from pathlib import Path

DART = Path(__file__).resolve().parent.parent / "mobile_app/lib/bev_socket.dart"


def _dart() -> str:
    return DART.read_text(encoding="utf-8")


def test_bev_socket_dart_exists() -> None:
    """mobile_app/lib/bev_socket.dart 파일 존재."""
    assert DART.exists(), "mobile_app/lib/bev_socket.dart 없음"


def test_bev_payload_class() -> None:
    """BevPayload — fps/frameIdx/tracks/device 필드."""
    d = _dart()
    assert "class BevPayload" in d, "BevPayload 없음"
    for field in ("fps", "frameIdx", "tracks", "device"):
        assert field in d, f"BevPayload.{field} 없음"


def test_bev_payload_person_vehicle_count() -> None:
    """BevPayload.personCount / vehicleCount getter."""
    d = _dart()
    assert "personCount" in d, "personCount getter 없음"
    assert "vehicleCount" in d, "vehicleCount getter 없음"


def test_bev_payload_person_per_bin() -> None:
    """BevPayload.personPerBin() — 칸별 점유 분할 메서드."""
    d = _dart()
    assert "personPerBin" in d, "personPerBin() 없음"


def test_socket_state_enum() -> None:
    """SocketState enum — disconnected/connecting/connected/error."""
    d = _dart()
    assert "enum SocketState" in d, "SocketState enum 없음"
    for state in ("disconnected", "connecting", "connected", "error"):
        assert state in d, f"SocketState.{state} 없음"


def test_arrival_row_eta_seconds() -> None:
    """ArrivalRow.etaSeconds getter — arvlCd=5→0 (당역도착)."""
    d = _dart()
    assert "etaSeconds" in d, "etaSeconds getter 없음"
    assert "arvlCd" in d, "arvlCd 필드 없음"
    assert "barvlDt" in d, "barvlDt 필드 없음"


def test_population_response_ppltn_mid() -> None:
    """PopulationResponse.ppltnMid — min/max 중간값 getter."""
    d = _dart()
    assert "class PopulationResponse" in d, "PopulationResponse 없음"
    assert "ppltnMid" in d, "ppltnMid getter 없음"


def test_bev_socket_ws_message_types() -> None:
    """BevSocket WS 메시지 타입 7종 정의."""
    d = _dart()
    for msg_type in (
        "arrival_query",
        "population_query",
        "citydata_query",
        "events_query",
        "impact_log",
        "phone_telemetry",
        "citizen_report",
    ):
        assert msg_type in d, f"WS 메시지 타입 '{msg_type}' 없음"


def test_citizen_report_flutter_source() -> None:
    """citizenReport() — source: 'flutter-app' 포함."""
    d = _dart()
    assert "flutter-app" in d, "citizenReport source='flutter-app' 없음"


def test_ngrok_header() -> None:
    """BevSocket.connect() — ngrok-skip-browser-warning 헤더."""
    d = _dart()
    assert "ngrok-skip-browser-warning" in d, "ngrok 우회 헤더 없음"
