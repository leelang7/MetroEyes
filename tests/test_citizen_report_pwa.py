"""passenger_app 시민 신고 FAB 기능 회귀 가드 (cycle 462, 475, 486).

cycle 443 시민 신고 FAB 기능:
- 분실물(lost) / 응급(emergency) / 배려(priority_seat) 3종 신고 버튼
- 30초 쿨다운 방지 (스팸 차단)
- citizen_report WS 페이로드 형식 검증
- 서버 미연결 시 오프라인 큐(localStorage) → 재연결 시 자동 전송
- 각 신고 타입 backend 수신 후 broadcast
cycle 486: admin.html 시민 신고 LIVE 패널 — citizen_report WS 실시간 표시 가드 추가
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PWA = ROOT / "frontend" / "passenger_app" / "index.html"
ADMIN = ROOT / "frontend" / "admin.html"


def _html() -> str:
    return PWA.read_text(encoding="utf-8")


def _admin() -> str:
    return ADMIN.read_text(encoding="utf-8")


def test_citizen_report_pwa_exists() -> None:
    """passenger_app/index.html 존재."""
    assert PWA.exists(), f"missing {PWA}"


def test_three_report_type_buttons() -> None:
    """분실물/응급/배려 3종 신고 버튼 존재."""
    html = _html()
    assert "분실물 신고" in html, "분실물 신고 버튼 누락"
    assert "응급 신고" in html, "응급 신고 버튼 누락"
    assert "배려 요청" in html, "배려 요청 버튼 누락"


def test_send_report_function_exists() -> None:
    """sendReport 또는 시민 신고 전송 함수 존재."""
    html = _html()
    assert "citizen_report" in html, "citizen_report WS 타입 누락"
    assert "incident_type" in html, "incident_type 페이로드 필드 누락"


def test_report_cooldown_mechanism() -> None:
    """30초 쿨다운 스팸 방지 메커니즘."""
    html = _html()
    m = re.search(r"30[,\s]*0{3}|30000|쿨다운|cooldown", html, re.IGNORECASE)
    assert m, "신고 쿨다운 메커니즘 누락 (30초 스팸 방지)"


def test_report_station_payload() -> None:
    """신고 페이로드에 station 필드 포함."""
    html = _html()
    m = re.search(r"citizen_report[\s\S]{0,500}?station", html)
    assert m, "citizen_report 페이로드에 station 필드 누락"


def test_offline_feedback_shown() -> None:
    """서버 미연결 시 오프라인 피드백 표시."""
    html = _html()
    assert "오프라인" in html, "오프라인 상태 피드백 누락"


def test_offline_queue_localStorage() -> None:
    """오프라인 큐 — localStorage 저장 후 재연결 시 자동 전송."""
    html = _html()
    assert "_REPORT_Q_KEY" in html or "metroeyes_report_queue" in html, \
        "오프라인 신고 큐 localStorage 키 누락"
    assert "flushReportQueue" in html, "flushReportQueue (재연결 시 큐 플러시) 함수 누락"
    assert "재연결 시 자동 전송" in html, "오프라인 큐 UX 피드백 메시지 누락"


def test_admin_citizen_report_panel_exists() -> None:
    """admin.html 에 시민 신고 LIVE 패널 존재 (양면 가치사슬 demo)."""
    html = _admin()
    assert "citizen-report-panel" in html or "시민 신고 LIVE" in html, \
        "admin.html 시민 신고 LIVE 패널 누락"
    assert "cr-em" in html, "시민 신고 응급 카운터 누락"
    assert "cr-lo" in html, "시민 신고 분실물 카운터 누락"
    assert "cr-ca" in html, "시민 신고 배려 카운터 누락"


def test_admin_handles_citizen_report_ws_type() -> None:
    """admin.html WS onmessage 가 citizen_report 타입 처리."""
    html = _admin()
    import re
    m = re.search(r"citizen_report[\s\S]{0,400}?cr-em|cr-em[\s\S]{0,400}?citizen_report", html)
    assert m, "admin.html onmessage 가 citizen_report 타입 라우팅 안 함"
