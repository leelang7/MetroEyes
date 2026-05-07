"""ad_pricing.html 환경 라이브 chip 회귀 (cycle 394).

backend citydata broadcast 의 PM2.5 / UV 를 광고 단가 페이지가 라이브 노출 →
"날씨/공기 modulation" insight 카드 + 헤더 chip 자동 표시.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AD = ROOT / "frontend" / "operator_web" / "ad_pricing.html"


def _ad() -> str:
    return AD.read_text(encoding="utf-8")


def test_env_pill_dom_present() -> None:
    """🌍 환경 chip + PM2.5 / UV 값 자리표시자 존재."""
    html = _ad()
    assert 'id="ad-env-pill"' in html, "env pill DOM missing"
    assert 'id="ad-env-pm25"' in html, "PM2.5 placeholder missing"
    assert 'id="ad-env-uv"' in html, "UV placeholder missing"


def test_env_handler_wired_to_ws() -> None:
    """citydata broadcast 의 pm25 / uv_idx 가 chip 채움."""
    html = _ad()
    assert "j.pm25 != null" in html, "PM2.5 detection logic missing"
    assert "j.uv_idx" in html, "UV detection logic missing"
    assert "ad-env-pill" in html, "pill toggle missing"


def test_env_modulation_insight_card_present() -> None:
    """광고 매체 modulation insight 카드 (지하 vs 지상 가치 역전)."""
    html = _ad()
    assert "🌍 날씨/공기 → 광고 매체 modulation" in html, "env modulation card missing"
    assert "지하" in html and "지상" in html, "지하/지상 modulation comparison missing"
    assert "PM2.5 ≥ 36" in html, "PM2.5 threshold (cycle 357 정합) missing"
    assert "UV ≥ 9" in html, "UV threshold (cycle 357 정합) missing"


def test_env_advertiser_value_documented() -> None:
    """광고주 가치 — ROAS +15~25% 등가 광고 단가 modulation 명시."""
    html = _ad()
    assert "ROAS" in html or "프리미엄" in html, "광고주 가치 표현 누락"
