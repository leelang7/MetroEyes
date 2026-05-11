"""lite_server 환경/신고 기능 회귀 가드 (cycle 446).

cycle 443 ~ 444 추가 기능:
  - fetch_indoor_air: IndoorAirQualityMeasureService API 연동
  - fetch_elevator_status: SubwayElevatorStatus API 연동
  - citizen_report WS 핸들러: 분실/응급/배려 신고 broadcast
  - _periodic_env_broadcast: 5분/2분 주기 환경 데이터 push
  - /api/v1/indoor_air, /api/v1/elevator, /api/v1/occupancy_forecast HTTP 엔드포인트
  - _predict_occupancy_24h: dict 반환 (hourly + peak_hour + cluster)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "src" / "cv" / "lite_server.py"


def _src() -> str:
    return SERVER.read_text(encoding="utf-8")


# ────────────────────────────────────────────
# fetch_indoor_air
# ────────────────────────────────────────────

def test_fetch_indoor_air_is_async() -> None:
    """fetch_indoor_air 는 async def — await 직접 호출 가능해야 함."""
    s = _src()
    assert "async def fetch_indoor_air(" in s, "fetch_indoor_air async def 누락"


def test_fetch_indoor_air_uses_correct_api() -> None:
    """IndoorAirQualityMeasureService or IndoorAirQuality 엔드포인트 호출."""
    s = _src()
    assert "IndoorAirQuality" in s, "IndoorAirQualityMeasureService API 호출 누락"


def test_fetch_indoor_air_returns_co2_fields() -> None:
    """co2_ppm + temp + co2 (alias) 필드 모두 포함."""
    s = _src()
    assert "co2_ppm" in s, "co2_ppm 필드 누락"
    assert '"co2"' in s or "'co2'" in s, "co2 alias 필드 누락"
    assert '"temp"' in s or "'temp'" in s, "temp 필드 누락"


def test_fetch_indoor_air_not_via_executor() -> None:
    """async def 이므로 run_in_executor 에 넘기면 안 됨 — await 직접 호출."""
    s = _src()
    # run_in_executor 호출부에 fetch_indoor_air 가 없어야 함
    bad = re.search(r"run_in_executor\([^)]*fetch_indoor_air", s)
    assert not bad, "fetch_indoor_air 가 run_in_executor 에 전달됨 — async/executor 버그"


# ────────────────────────────────────────────
# fetch_elevator_status
# ────────────────────────────────────────────

def test_fetch_elevator_status_is_async() -> None:
    """fetch_elevator_status 는 async def."""
    s = _src()
    assert "async def fetch_elevator_status(" in s, "fetch_elevator_status async def 누락"


def test_fetch_elevator_status_not_via_executor() -> None:
    """async def 이므로 run_in_executor 에 넘기면 안 됨."""
    s = _src()
    bad = re.search(r"run_in_executor\([^)]*fetch_elevator_status", s)
    assert not bad, "fetch_elevator_status 가 run_in_executor 에 전달됨 — async/executor 버그"


def test_fetch_elevator_status_returns_elevator_list() -> None:
    """elevator_list / elevators 필드 반환."""
    s = _src()
    assert "elevator" in s.lower(), "elevator 필드 누락"


# ────────────────────────────────────────────
# citizen_report WS 핸들러
# ────────────────────────────────────────────

def test_citizen_report_handler_exists() -> None:
    """citizen_report 메시지 타입 핸들러 분기 존재."""
    s = _src()
    assert "citizen_report" in s, "citizen_report WS 핸들러 누락"


def test_citizen_report_broadcasts_to_clients() -> None:
    """신고 수신 시 운영자 콘솔에 broadcast (clients 루프 또는 broadcast 함수)."""
    s = _src()
    # citizen_report 분기 안에 broadcast 또는 clients 가 있어야 (창 1500자)
    m = re.search(r'citizen_report["\'][\s\S]{0,1500}?(broadcast|clients)', s)
    assert m, "citizen_report 핸들러가 broadcast/clients 에 전달하지 않음"


def test_citizen_report_updates_incident_total() -> None:
    """신고 → _incident_total 누적."""
    s = _src()
    m = re.search(r'citizen_report["\'][\s\S]{0,1200}?_incident_total', s)
    assert m, "citizen_report 핸들러가 _incident_total 갱신 안 함"


# ────────────────────────────────────────────
# _periodic_env_broadcast
# ────────────────────────────────────────────

def test_periodic_env_broadcast_exists() -> None:
    """_periodic_env_broadcast 비동기 태스크 정의."""
    s = _src()
    assert "_periodic_env_broadcast" in s, "_periodic_env_broadcast 태스크 누락"


def test_periodic_env_broadcast_schedules_indoor_air() -> None:
    """_periodic_env_broadcast 내부에서 fetch_indoor_air 호출."""
    s = _src()
    m = re.search(r"_periodic_env_broadcast[\s\S]{0,1200}?fetch_indoor_air", s)
    assert m, "_periodic_env_broadcast 가 fetch_indoor_air 호출 안 함"


def test_periodic_env_broadcast_schedules_elevator() -> None:
    """_periodic_env_broadcast 내부에서 fetch_elevator_status 호출."""
    s = _src()
    m = re.search(r"_periodic_env_broadcast[\s\S]{0,1200}?fetch_elevator_status", s)
    assert m, "_periodic_env_broadcast 가 fetch_elevator_status 호출 안 함"


# ────────────────────────────────────────────
# HTTP endpoints
# ────────────────────────────────────────────

def test_http_indoor_air_endpoint() -> None:
    """/api/v1/indoor_air HTTP 엔드포인트 경로 존재."""
    s = _src()
    assert "/api/v1/indoor_air" in s, "/api/v1/indoor_air 엔드포인트 누락"


def test_http_elevator_endpoint() -> None:
    """/api/v1/elevator HTTP 엔드포인트 경로 존재."""
    s = _src()
    assert "/api/v1/elevator" in s, "/api/v1/elevator 엔드포인트 누락"


def test_http_occupancy_forecast_endpoint() -> None:
    """/api/v1/occupancy_forecast HTTP 엔드포인트 경로 존재."""
    s = _src()
    assert "/api/v1/occupancy_forecast" in s, "/api/v1/occupancy_forecast 엔드포인트 누락"


# ────────────────────────────────────────────
# _predict_occupancy_24h dict 반환
# ────────────────────────────────────────────

def test_predict_occupancy_24h_returns_dict() -> None:
    """_predict_occupancy_24h 함수가 dict 반환 (hourly, peak_hour, cluster 키)."""
    s = _src()
    assert "_predict_occupancy_24h" in s, "_predict_occupancy_24h 함수 누락"
    # dict 반환 — 'hourly' 키 존재
    m = re.search(r"_predict_occupancy_24h[\s\S]{0,2000}?[\"']hourly[\"']", s)
    assert m, "_predict_occupancy_24h 가 hourly 키 포함 dict 반환 안 함"


def test_predict_occupancy_24h_includes_cluster() -> None:
    """_predict_occupancy_24h 반환값에 cluster 정보 포함."""
    s = _src()
    m = re.search(r"_predict_occupancy_24h[\s\S]{0,2000}?[\"']cluster[\"']", s)
    assert m, "_predict_occupancy_24h 가 cluster 키 포함 안 함"


# ────────────────────────────────────────────
# /health data_sources count
# ────────────────────────────────────────────

def test_health_data_sources_count_10() -> None:
    """서버 /health 응답에 data_sources: 10 명시."""
    s = _src()
    assert "data_sources" in s, "/health 에 data_sources 키 없음"
    # 10 이상
    m = re.search(r'data_sources["\s:]+(\d+)', s)
    assert m and int(m.group(1)) >= 10, f"data_sources 카운트 10 미만: {m}"
