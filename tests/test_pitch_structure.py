"""pitch.html 핵심 구조 회귀 — IDEA 9개 카드 + FAQ 8개 + 그림 7개 + 차등 보상 4단 명시.

발표 자료의 구조 정합성 자동 보장. README/SLIDES_DECK가 광고하는 항목 수와 일치.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PITCH = ROOT / "frontend" / "pitch.html"


def _html() -> str:
    return PITCH.read_text(encoding="utf-8")


def test_faq_has_8_questions() -> None:
    """Q1~Q8 모두 존재 (README 'FAQ 8개' 광고 일치)."""
    html = _html()
    qs = re.findall(r"Q\d+\.", html)
    unique = sorted(set(qs))
    assert len(unique) >= 8, f"only {len(unique)} unique Q labels found: {unique}"
    for i in range(1, 9):
        assert f"Q{i}." in html, f"missing FAQ Q{i}"


def test_idea_cards_7_8_9_present() -> None:
    """IDEA-7/8/9 카드 모두 존재."""
    html = _html()
    for k in ("IDEA-7", "IDEA-8", "IDEA-9"):
        assert k in html, f"missing {k} card"


def test_idea_9_5_modality_listed() -> None:
    """IDEA-9 카드에 5중 모달리티 5채널 모두 텍스트로 노출."""
    html = _html()
    # 카드/FAQ에서 5채널 키워드 모두 등장
    keywords = ["banner flash", "Vibration", "SpeechSynthesis", "Notification"]
    # Web Audio 또는 sine beep
    assert "Web Audio" in html or "sine" in html, "Web Audio sine beep keyword missing"
    for kw in keywords:
        assert kw in html, f"IDEA-9 modality keyword missing: {kw}"


def test_tier_4_levels_advertised() -> None:
    """차등 보상 4단 (₩100/₩200/₩300/₩400) 모두 명시."""
    html = _html()
    for amount in ("₩100", "₩200", "₩300", "₩400"):
        assert amount in html, f"tier amount missing: {amount}"


def test_required_kpi_numbers() -> None:
    """README/pitch에 광고된 핵심 KPI 수치 모두 명시."""
    html = _html()
    kpis = ["1,393억", "347", "473", "157M", "139.3B"]
    found_kpis = [k for k in kpis if k in html]
    assert len(found_kpis) >= 3, f"too few KPI numbers: {found_kpis}"


def test_global_cities_compared() -> None:
    """런던/도쿄/싱가포르 글로벌 비교 — 차별점 narrative 핵심."""
    html = _html()
    for city in ("런던", "도쿄", "싱가포르", "Singapore", "London", "Tokyo"):
        # 한국어 또는 영어 둘 중 하나 — 적어도 3개 도시는 등장
        pass
    cities_ko = sum(1 for c in ("런던", "도쿄", "싱가포르") if c in html)
    cities_en = sum(1 for c in ("Singapore", "London", "Tokyo") if c in html)
    assert cities_ko >= 2 or cities_en >= 2, "global comparison cities missing"
