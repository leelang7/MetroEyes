"""ad_pricing.html 의 AI 자동 단가 근거 카드 회귀 (cycle 356).

backend tesla_bev.py 가 폭증 감지 시 broadcast 하는 type='context' 메시지를
ad_pricing.html 가 수신해 광고주 단가 근거 카드로 노출하는지 정합성 보장.

장애 시나리오: 핸들러 누락 / 로컬스토리지 키 변경 / 타입 매칭 실패.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AD = ROOT / "frontend" / "operator_web" / "ad_pricing.html"
ADMIN = ROOT / "frontend" / "admin.html"
TESLA = ROOT / "src" / "cv" / "tesla_bev.py"


def _ad() -> str:
    return AD.read_text(encoding="utf-8")


def _admin() -> str:
    return ADMIN.read_text(encoding="utf-8")


def _tesla() -> str:
    return TESLA.read_text(encoding="utf-8")


def test_ad_llm_card_present() -> None:
    """광고주 페이지에 AI 자동 단가 근거 카드 DOM 존재."""
    html = _ad()
    for el_id in ("ad-llm-card", "ad-llm-poi", "ad-llm-text", "ad-llm-ts", "ad-llm-trigger"):
        assert f'id="{el_id}"' in html, f"missing element id: {el_id}"


def test_ad_llm_handler_wired_to_ws() -> None:
    """ad_pricing.html WS onmessage 가 context/llm 메시지를 처리."""
    html = _ad()
    assert "applyAdLlmContext" in html, "applyAdLlmContext function missing"
    # 메시지 타입 매칭 — backend tesla_bev.py 가 type='context' 로 보냄
    assert "j.type === 'context'" in html, "context type match missing"
    assert "j.summary" in html, "summary fallback missing"


def test_ad_llm_localstorage_persistence() -> None:
    """직전 컨텍스트 새 탭 복원 — localStorage AD_LLM_KEY."""
    html = _ad()
    assert "AD_LLM_KEY" in html, "localStorage key constant missing"
    assert "localStorage.setItem(AD_LLM_KEY" in html, "localStorage write missing"
    assert "localStorage.getItem(AD_LLM_KEY)" in html, "localStorage read missing"


def test_admin_context_type_match_fixed() -> None:
    """admin.html 도 backend 의 type='context' 를 매칭 (cycle 356 fix)."""
    html = _admin()
    # cycle 355 버그: 'surge_context'/'llm_context' 만 매칭 → type='context' 누락
    assert "t === 'context'" in html, "admin must match backend type='context'"
    assert "j.summary" in html, "admin must accept j.summary as fallback text"


def test_backend_broadcasts_context_with_summary() -> None:
    """backend tesla_bev.py 의 폭증 broadcast payload 는 type='context' + summary."""
    src = _tesla()
    assert '"type": "context"' in src, "backend must broadcast type='context'"
    assert '"summary":' in src, "backend payload must include summary field"
    # 폭증 트리거 → broadcast
    assert "fetch_context_news" in src, "context fetch trigger missing"
