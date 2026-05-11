"""src/cv/lite_server.py 구조 회귀 가드 (cycle 514).

torch/ultralytics 없이 실행 — 외부 API 라이브 호출 전용 경량 서버.
핵심 WS 메시지 타입 / 공유 상태 / 차등 보상 로직 검증.

네트워크 불필요: 모듈 소스 코드 구조 분석.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LITE_SRC = ROOT / "src" / "cv" / "lite_server.py"


def _src() -> str:
    return LITE_SRC.read_text(encoding="utf-8")


def test_lite_server_exists() -> None:
    """src/cv/lite_server.py 존재."""
    assert LITE_SRC.is_file(), "lite_server.py 누락"


def test_lite_server_ws_message_types() -> None:
    """핵심 WS 메시지 타입 — arrival/population/citydata/events/impact_log."""
    src = _src()
    for msg_type in ("arrival_query", "population_query", "citydata_query",
                     "events_query", "impact_log"):
        assert msg_type in src, f"WS 메시지 타입 {msg_type} 누락"


def test_lite_server_no_torch_import() -> None:
    """torch/ultralytics import 없음 — 경량 서버 조건 충족."""
    src = _src()
    assert "import torch" not in src, "torch import 있음 — 경량 서버 위반"
    assert "from ultralytics" not in src, "ultralytics import 있음 — 경량 서버 위반"


def test_lite_server_bonus_krw_function() -> None:
    """_bonus_krw 차등 인센티브 함수 — OD/환승 가산 보상."""
    src = _src()
    assert "_bonus_krw" in src, "_bonus_krw 차등 인센티브 함수 누락"


def test_lite_server_seoul_key_env() -> None:
    """SEOUL_OPENDATA_API_KEY 환경변수 참조."""
    src = _src()
    assert "SEOUL_OPENDATA_API_KEY" in src, "SEOUL_OPENDATA_API_KEY 환경변수 참조 누락"


def test_lite_server_impact_broadcast() -> None:
    """impact_log → 누적 임팩트 broadcast."""
    src = _src()
    assert "impact_log" in src, "impact_log 핸들러 누락"
    assert "impact" in src.lower(), "임팩트 누적 로직 누락"


def test_lite_server_context_cache() -> None:
    """context_cache — 네이버 뉴스/LLM 결과 TTL 캐시."""
    src = _src()
    assert "context_cache" in src, "context_cache 누락"
    assert "CONTEXT_TTL" in src, "CONTEXT_TTL 누락"


def test_lite_server_fake_bev_loop() -> None:
    """fake_bev_loop — 시연 모드 BEV 시뮬 브로드캐스트."""
    src = _src()
    assert "fake_bev" in src or "demo" in src.lower(), "fake_bev 시연 루프 누락"


def test_lite_server_health_endpoint() -> None:
    """/health HTTP 엔드포인트 — CV fps/clients/api 상태."""
    src = _src()
    assert "/health" in src, "/health 엔드포인트 누락"


def test_lite_server_argparse_port() -> None:
    """--port 인자 (기본 8765) argparse."""
    src = _src()
    assert "--port" in src, "--port 인자 누락"
    assert "8765" in src, "기본 포트 8765 누락"
