"""src/api/main.py FastAPI 라우트 회귀 가드 (cycle 507).

서버 기동 없이 FastAPI app 객체 직접 검증:
- 앱 타이틀: MetroEyes API
- CORS 미들웨어 설정
- 라우트 등록: /health, /api/cars/{train_id}, /ws/bev
- 응답 구조 (TestClient 활용)
"""
from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from src.api.main import app
    with TestClient(app) as c:
        yield c


def test_app_title() -> None:
    """FastAPI app.title == 'MetroEyes API'."""
    from src.api.main import app
    assert app.title == "MetroEyes API"


def test_app_version() -> None:
    """FastAPI app.version == '0.0.1'."""
    from src.api.main import app
    assert app.version == "0.0.1"


def test_health_route_registered() -> None:
    """/health 라우트 등록 확인."""
    from src.api.main import app
    paths = [r.path for r in app.routes]
    assert "/health" in paths, "/health 라우트 누락"


def test_cars_route_registered() -> None:
    """/api/cars/{train_id} 라우트 등록 확인."""
    from src.api.main import app
    paths = [r.path for r in app.routes]
    assert "/api/cars/{train_id}" in paths, "/api/cars 라우트 누락"


def test_ws_bev_route_registered() -> None:
    """/ws/bev WebSocket 라우트 등록 확인."""
    from src.api.main import app
    paths = [r.path for r in app.routes]
    assert "/ws/bev" in paths, "/ws/bev WebSocket 라우트 누락"


def test_health_endpoint_returns_ok(client) -> None:
    """/health GET → {"status": "ok"}."""
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "ts" in data


def test_car_status_endpoint(client) -> None:
    """/api/cars/T001 GET → 10칸 응답."""
    r = client.get("/api/cars/T001")
    assert r.status_code == 200
    data = r.json()
    assert data["train_id"] == "T001"
    assert len(data["cars"]) == 10


def test_car_status_car_fields(client) -> None:
    """각 칸 응답에 car_no/occupancy/count/density 포함."""
    r = client.get("/api/cars/X999")
    data = r.json()
    car = data["cars"][0]
    for field in ("car_no", "occupancy", "count", "density"):
        assert field in car, f"칸 응답 {field} 필드 누락"


def test_cors_middleware_present() -> None:
    """CORSMiddleware 등록 확인."""
    from src.api.main import app
    middleware_types = [m.cls.__name__ for m in app.user_middleware]
    assert "CORSMiddleware" in middleware_types, "CORSMiddleware 미등록"
