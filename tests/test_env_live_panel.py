"""admin.html 환경 라이브 패널 회귀 (cycle 357).

backend tesla_bev.py 의 type='citydata' broadcast 에 pm25/pm10/air_idx/uv_idx/temp/humidity 가
이미 포함되어 있고, admin.html 가 수신해 PM/UV/온도 카드를 라이브 갱신한다.

장애 시나리오: 카드 DOM 누락 / 핸들러 미연결 / backend payload 필드 변경.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADMIN = ROOT / "frontend" / "admin.html"
TESLA = ROOT / "src" / "cv" / "tesla_bev.py"


def _admin() -> str:
    return ADMIN.read_text(encoding="utf-8")


def _tesla() -> str:
    return TESLA.read_text(encoding="utf-8")


def test_env_panel_dom_present() -> None:
    html = _admin()
    for el_id in ("env-pm25", "env-pm10", "env-air", "env-uv", "env-temp", "env-hum", "env-poi", "env-alert"):
        assert f'id="{el_id}"' in html, f"missing env panel id: {el_id}"


def test_env_handler_wired() -> None:
    html = _admin()
    assert "applyEnvLive" in html, "applyEnvLive function missing"
    # citydata broadcast 시 호출
    assert "if (t === 'citydata') applyEnvLive(j);" in html, "citydata trigger missing"


def test_env_alert_thresholds() -> None:
    """약자 보호 알림 임계 — PM2.5 36 / PM10 81 / UV lvl 9."""
    html = _admin()
    assert "j.pm25 >= 36" in html, "PM2.5 bad threshold missing"
    assert "j.pm10 >= 81" in html, "PM10 bad threshold missing"
    assert "uv_lvl ?? 0) >= 9" in html or "uv_lvl??0) >= 9" in html, "UV very-high threshold missing"


def test_backend_citydata_broadcasts_env_fields() -> None:
    """backend tesla_bev.py 가 citydata payload 에 환경 필드를 포함한다."""
    src = _tesla()
    assert '"type": "citydata"' in src, "backend must broadcast type='citydata'"
    # 환경 필드 — admin 가 의존
    for f in ('"pm25":', '"pm10":', '"air_idx":', '"uv_idx":', '"temp":', '"humidity":'):
        assert f in src, f"backend payload field missing: {f}"
