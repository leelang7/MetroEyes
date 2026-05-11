"""operator_web/admin.html WS 핸들러 회귀 가드 (cycle 447).

cycle 446 admin.html 은 bev/bus_bev/incident/indoor_air/elevator_status 만 처리.
cycle 447: incident_summary / occupancy_forecast / env_broadcast WS 핸들러 추가.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADMIN = ROOT / "frontend" / "operator_web" / "admin.html"


def _html() -> str:
    return ADMIN.read_text(encoding="utf-8")


def test_admin_op_exists() -> None:
    """operator_web/admin.html 파일 존재."""
    assert ADMIN.exists(), f"missing {ADMIN}"


def test_handle_msg_routes_incident_summary() -> None:
    """handleMsg 가 incident_summary 타입을 applyIncidentSummary 로 라우팅."""
    html = _html()
    assert "incident_summary" in html, "incident_summary 라우팅 누락"
    assert "applyIncidentSummary" in html, "applyIncidentSummary 함수 누락"


def test_handle_msg_routes_occupancy_forecast() -> None:
    """handleMsg 가 occupancy_forecast 타입을 drawForecast 로 라우팅."""
    html = _html()
    m = re.search(r"handleMsg[\s\S]{0,500}?occupancy_forecast[\s\S]{0,200}?drawForecast", html)
    assert m, "handleMsg 가 occupancy_forecast → drawForecast 라우팅 안 함"


def test_handle_msg_routes_env_broadcast() -> None:
    """handleMsg 가 env_broadcast 타입을 applyEnvBroadcast 로 라우팅."""
    html = _html()
    assert "env_broadcast" in html, "env_broadcast 라우팅 누락"
    assert "applyEnvBroadcast" in html, "applyEnvBroadcast 함수 누락"


def test_apply_incident_summary_updates_kpi() -> None:
    """applyIncidentSummary 가 kpi-inc 카운터를 갱신."""
    html = _html()
    m = re.search(r"applyIncidentSummary[\s\S]{0,500}?kpi-inc", html)
    assert m, "applyIncidentSummary 가 kpi-inc 갱신 안 함"


def test_apply_incident_summary_appends_events() -> None:
    """applyIncidentSummary 가 events 배열 → appendIncident 호출."""
    html = _html()
    m = re.search(r"applyIncidentSummary[\s\S]{0,600}?appendIncident", html)
    assert m, "applyIncidentSummary 가 appendIncident 호출 안 함"


def test_apply_env_broadcast_calls_apply_air() -> None:
    """applyEnvBroadcast 가 d.air → applyAir 라우팅."""
    html = _html()
    m = re.search(r"applyEnvBroadcast[\s\S]{0,300}?applyAir", html)
    assert m, "applyEnvBroadcast 가 applyAir 호출 안 함"


def test_apply_env_broadcast_calls_apply_elev() -> None:
    """applyEnvBroadcast 가 d.elevator → applyElev 라우팅."""
    html = _html()
    m = re.search(r"applyEnvBroadcast[\s\S]{0,300}?applyElev", html)
    assert m, "applyEnvBroadcast 가 applyElev 호출 안 함"


def test_ws_init_sequence() -> None:
    """페이지 로드 시 connectWs + fetchAir + fetchElev + fetchForecast + fetchApiHealth 호출."""
    html = _html()
    for fn in ("connectWs()", "fetchAir()", "fetchElev()", "fetchForecast()", "fetchApiHealth()"):
        assert fn in html, f"init sequence 누락: {fn}"


def test_forecast_canvas_element_exists() -> None:
    """fc-canvas element + drawForecast 함수 정의."""
    html = _html()
    assert 'id="fc-canvas"' in html, "fc-canvas element 누락"
    assert "function drawForecast(" in html, "drawForecast 함수 누락"


def test_incident_log_resolve_button() -> None:
    """인시던트 해결 버튼 존재 (resolveInc)."""
    html = _html()
    assert "resolveInc" in html, "resolveInc 버튼 핸들러 누락"


def test_social_impact_panel_exists() -> None:
    """사회적 가치 임팩트 패널 DOM + fetchImpact 함수."""
    html = _html()
    assert "사회적 가치 임팩트" in html, "사회적 가치 임팩트 패널 제목 누락"
    assert 'id="imp-count"' in html, "imp-count element 누락"
    assert 'id="imp-krw"' in html, "imp-krw element 누락"
    assert 'id="imp-roi"' in html, "imp-roi element 누락"
    assert "function fetchImpact(" in html, "fetchImpact 함수 누락"


def test_social_impact_calls_impact_api() -> None:
    """fetchImpact 가 /api/v1/impact 호출."""
    html = _html()
    assert "/api/v1/impact" in html, "/api/v1/impact 호출 누락"


def test_social_impact_shows_tier_breakdown() -> None:
    """fetchImpact 가 기본/OD/환승 tier 분포 표시."""
    html = _html()
    assert "tier_counts" in html, "tier_counts 파싱 누락"
    assert "imp-tier" in html, "imp-tier element 누락"


def test_social_impact_polled_every_minute() -> None:
    """fetchImpact 1분 주기 폴링."""
    html = _html()
    assert "setInterval(fetchImpact" in html, "fetchImpact setInterval 누락"


def test_append_incident_loc_precedence_fixed() -> None:
    """appendIncident loc 산출: d.location 우선, 마지막에만 d.car 호차 fallback."""
    html = _html()
    assert "d.location || d.station || (d.car" in html, \
        "appendIncident loc 연산자 우선순위 버그 (d.location truthy 시 d.car호차 오표시)"
