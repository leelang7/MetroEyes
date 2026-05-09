"""citydata 통합 API 회귀 가드 (cycle 427).

cycle 426 까지: lite_server 의 citydata_query 가 실제 citydata API 호출 X — 인구만 type 바꿔치기로 반환.
cycle 427: fetch_citydata() 신규 — WEATHER_STTS / EVENT_STTS / ROAD_TRAFFIC_STTS / LIVE_PPLTN_STTS 통합 추출.

광고 단가 페이지 (frontend/operator_web/ad_pricing.html) PM2.5/UV chip 라이브 수신 가능.
시민 PWA events_query 응답에 실제 EVENT_STTS 채워짐.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "src" / "cv" / "lite_server.py"


def _src() -> str:
    return SERVER.read_text(encoding="utf-8")


def test_fetch_citydata_function_defined() -> None:
    """fetch_citydata async 함수 정의."""
    s = _src()
    assert "async def fetch_citydata(" in s, "fetch_citydata 함수 누락"


def test_fetch_citydata_uses_citydata_endpoint_not_ppltn() -> None:
    """/json/citydata/ 엔드포인트 (citydata_ppltn 아님 — 통합 응답)."""
    s = _src()
    assert "/json/citydata/" in s, \
        "fetch_citydata 가 /json/citydata/ 엔드포인트 호출 안 함 (citydata_ppltn 만 부르면 통합 데이터 못 받음)"


def test_fetch_citydata_extracts_weather_fields() -> None:
    """WEATHER_STTS 추출 (PM25/PM10/UV/TEMP)."""
    s = _src()
    assert "WEATHER_STTS" in s, "WEATHER_STTS 파싱 누락"
    for field in ("PM25", "PM10", "TEMP"):
        assert field in s, f"WEATHER 필드 {field} 추출 누락"
    # ad_pricing.html 가 기다리는 출력 키
    assert '"pm25"' in s, "응답 pm25 키 누락 (광고 페이지 chip 수신 실패)"
    assert '"uv_idx"' in s, "응답 uv_idx 키 누락"


def test_fetch_citydata_extracts_events() -> None:
    """EVENT_STTS 추출 → events 배열."""
    s = _src()
    assert "EVENT_STTS" in s, "EVENT_STTS 파싱 누락"
    assert "EVENT_NM" in s, "EVENT_NM 추출 누락"
    assert "EVENT_PLACE" in s, "EVENT_PLACE 추출 누락"


def test_citydata_query_handler_uses_real_fetch() -> None:
    """citydata_query 핸들러가 fetch_citydata 호출 (이전엔 fetch_population fake)."""
    s = _src()
    # citydata_query 분기 안에 fetch_citydata 호출
    m = re.search(r't\s*==\s*"citydata_query"[^}]*?fetch_citydata', s, re.DOTALL)
    assert m, "citydata_query 핸들러가 fetch_citydata 안 부름 (fake population 그대로)"


def test_events_query_handler_uses_real_fetch() -> None:
    """events_query 핸들러가 빈 배열 하드코딩 X — fetch_citydata 로 EVENT_STTS 추출."""
    s = _src()
    # events_query 분기 안에 fetch_citydata 또는 cd.get("events") 호출
    m = re.search(r't\s*==\s*"events_query"[^}]*?fetch_citydata', s, re.DOTALL)
    assert m, "events_query 핸들러가 fetch_citydata 호출 X — 빈 배열 fallback 만 남아 있음"


def test_api_track_includes_citydata() -> None:
    """API 호출 추적이 citydata 도 기록 (citydata_ppltn 와 별개로)."""
    s = _src()
    assert '_api_track("citydata"' in s, "citydata _api_track 누락"
