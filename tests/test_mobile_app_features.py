"""mobile_app Flutter 기능 회귀 가드 (cycle 473).

Flutter 네이티브 앱의 핵심 기능:
- 시민 신고 FAB (분실/응급/배려 3종)
- BEV WebSocket 클라이언트 (bev_socket.dart)
- citizenReport WS 메서드
- 역 GPS 자동 매칭
- population_query WS 메서드
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "mobile_app" / "lib" / "main.dart"
BEV_SOCKET = ROOT / "mobile_app" / "lib" / "bev_socket.dart"
README = ROOT / "mobile_app" / "README.md"


def _main() -> str:
    return MAIN.read_text(encoding="utf-8") if MAIN.exists() else ""


def _bev() -> str:
    return BEV_SOCKET.read_text(encoding="utf-8") if BEV_SOCKET.exists() else ""


def _readme() -> str:
    return README.read_text(encoding="utf-8") if README.exists() else ""


def test_mobile_app_exists() -> None:
    """mobile_app Flutter 앱 파일 존재."""
    assert MAIN.exists(), f"missing {MAIN}"
    assert BEV_SOCKET.exists(), f"missing {BEV_SOCKET}"


def test_citizen_report_fab_three_types() -> None:
    """시민 신고 FAB — 분실/응급/배려 3종 타입 존재."""
    s = _main()
    assert "응급 신고" in s or "emergency" in s, "emergency type missing in mobile_app"
    assert "분실물 신고" in s or "lost" in s, "lost type missing in mobile_app"
    assert "배려" in s or "priority_seat" in s, "priority_seat type missing in mobile_app"


def test_citizen_report_ws_method() -> None:
    """citizenReport WS 메서드 bev_socket.dart 에 정의."""
    s = _bev()
    assert "citizenReport" in s, "citizenReport method missing from bev_socket.dart"
    assert "citizen_report" in s, "citizen_report WS type missing from bev_socket.dart"


def test_population_query_ws() -> None:
    """population_query WS 메서드 존재."""
    s = _bev()
    assert "population_query" in s or "populationQuery" in s, \
        "population_query WS method missing from bev_socket.dart"


def test_readme_documents_ws_protocol() -> None:
    """mobile_app README에 citizen_report WS 프로토콜 명시."""
    s = _readme()
    assert "citizen_report" in s, "citizen_report WS 프로토콜 README 누락"
    assert "impact_log" in s, "impact_log WS 프로토콜 README 누락"
