"""admin.html + ad_pricing.html 4언어 i18n 정합성 회귀 (cycle 365).

cycle 356-360 신규 패널 (AI 4축 / ESG 라이브 / 환경 라이브 / LLM 컨텍스트 / AI 자동 단가)
헤더 라벨이 4언어 (ko/en/zh/ja) 모두 정의되어 있는지 검증.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADMIN = ROOT / "frontend" / "admin.html"
AD = ROOT / "frontend" / "operator_web" / "ad_pricing.html"


def _admin() -> str:
    return ADMIN.read_text(encoding="utf-8")


def _ad() -> str:
    return AD.read_text(encoding="utf-8")


def _extract_lang_block(html: str, dict_name: str, lang: str) -> str:
    """I18N_X 안의 lang: { ... } 블록 추출."""
    m = re.search(
        rf"const {dict_name} = \{{(.*?)\}};",
        html, re.DOTALL,
    )
    assert m, f"missing dict {dict_name}"
    body = m.group(1)
    # lang: { ... } 블록
    lm = re.search(rf"\b{lang}: \{{(.*?)\}},", body, re.DOTALL)
    assert lm, f"{dict_name} missing lang {lang}"
    return lm.group(1)


def test_admin_4lang_panel_keys() -> None:
    """admin I18N_ADMIN 4언어 모두 ai_h/esg_h/env_h/llm_h 정의."""
    html = _admin()
    for lang in ("ko", "en", "zh", "ja"):
        block = _extract_lang_block(html, "I18N_ADMIN", lang)
        for key in ("ai_h", "esg_h", "env_h", "llm_h", "sub", "btn"):
            assert f"{key}:" in block, f"I18N_ADMIN.{lang} missing {key}"


def test_admin_data_i18n_attrs_present() -> None:
    """env/AI/ESG/LLM 헤더 DOM 에 data-i18n 부착됨."""
    html = _admin()
    for k in ("ai_h", "esg_h", "env_h", "llm_h"):
        assert f'data-i18n="{k}"' in html, f"missing data-i18n: {k}"


def test_admin_apply_i18n_loops_data_i18n() -> None:
    """applyAdminI18n 가 data-i18n 요소를 순회하며 갱신."""
    html = _admin()
    assert "applyAdminI18n" in html, "applyAdminI18n function missing"
    assert "querySelectorAll('[data-i18n]')" in html, "data-i18n loop missing"


def test_ad_pricing_llm_card_4lang() -> None:
    """ad_pricing I18N_OP_AD 4언어 모두 ad_llm_h 정의."""
    html = _ad()
    for lang in ("ko", "en", "zh", "ja"):
        block = _extract_lang_block(html, "I18N_OP_AD", lang)
        for key in ("ad_llm_h", "ad_llm_intro"):
            assert f"{key}:" in block, f"I18N_OP_AD.{lang} missing {key}"


def test_ad_pricing_data_i18n_card_attrs() -> None:
    """ad LLM card 의 헤더/intro 에 data-i18n 부착."""
    html = _ad()
    assert 'data-i18n="ad_llm_h"' in html, "ad_llm_h data-i18n attr missing"
    assert 'data-i18n="ad_llm_intro"' in html, "ad_llm_intro data-i18n attr missing"


def test_ad_pricing_innerhtml_handling() -> None:
    """HTML <b> 가 포함된 i18n 값을 innerHTML 로 처리."""
    html = _ad()
    assert "el.innerHTML = t[k]" in html, "innerHTML branch missing for HTML strings"
    assert "el.textContent = t[k]" in html, "textContent branch missing for plain strings"
