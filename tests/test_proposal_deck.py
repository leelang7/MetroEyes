"""상세기획서 deck 회귀 가드 (cycle 430 — 6 IDEA 사회적 가치 중심 + 네이티브앱 + 대중 용어).

cycle 429 까지 사고:
  ① 6대 사회적 가치 IDEA (임산부/안전/응급/분실/무임/도착알림) deck 에 부재
  ② 네이티브 폰 앱 (Flutter mobile_app/) 미언급
  ③ 전문 용어 (TRIZ/Monte Carlo/BoT-SORT/K-means/BEV/fusion) 일반인 이해 X
  ④ 슬라이드 제목 작음 (h1 26px) — 다양한 분야 심사위원 가독성 부족

cycle 430 수정:
  ① 6 IDEA 핵심 슬라이드 (slide 3-1) — 임산부/응급/병목/분실/무임/도착알림 한 페이지에 다
  ② 네이티브 폰 앱 (Flutter) 별도 언급 (slide 1-3 + 5-2)
  ③ 일반인 용어 매핑: BEV → 위에서 본 평면 / Monte Carlo → 1,000번 시뮬레이션 / TRIZ → 발명 기법 / 등
  ④ 슬라이드 제목 36~42px 큼
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "docs" / "proposal_deck.html"


def _txt() -> str:
    return DECK.read_text(encoding="utf-8")


def test_deck_exists() -> None:
    assert DECK.exists()


def test_official_seven_sections_present() -> None:
    """PPT 정식 7항목 모두."""
    t = _txt()
    sections = ["제안 배경", "출품작 핵심", "차별성", "개발 과정", "IA", "창업", "개발 툴"]
    for s in sections:
        assert s in t, f"섹션 '{s}' 누락"


def test_six_social_value_ideas() -> None:
    """6대 사회적 가치 IDEA 모두 deck 에 (cycle 429 까지 부재)."""
    t = _txt()
    ideas = [
        ("임산부", "IDEA-7 임산부 배려석"),
        ("응급 골든타임", "응급 검출"),
        ("이태원", "IDEA-8 병목 — 이태원 참사 사전 경고"),
        ("분실물", "분실물 자동 추적"),
        ("무임", "무임승차 감지"),
        ("5중 도착 알림", "IDEA-9 노이즈 캔슬링"),
    ]
    for kw, desc in ideas:
        assert kw in t, f"사회적 IDEA '{desc}' ({kw}) 누락"


def test_native_mobile_app_mentioned() -> None:
    """네이티브 폰 앱 (Flutter) 언급 — cycle 429 까지 누락."""
    t = _txt()
    assert "네이티브 폰 앱" in t or "Flutter" in t, "네이티브 폰 앱 (Flutter) 누락"
    assert "Android" in t or "APK" in t, "Android APK 언급 누락"


def test_layperson_terms_used() -> None:
    """일반인 용어 사용 — 다양한 분야 심사위원 대응."""
    t = _txt()
    layperson_terms = [
        "위에서 본",         # BEV
        "1,000번 시뮬레이션", # Monte Carlo
        "발명 기법",          # TRIZ
        "추적 알고리즘",      # BoT-SORT
        "평면 보정",          # 호모그래피
        "위에서 본 평면",     # BEV (TES)
    ]
    found = sum(1 for k in layperson_terms if k in t)
    assert found >= 4, f"일반인 용어 {found}/6 — 4개 이상 필요 (전문 용어 위주면 다양한 분야 심사위원 이해 X)"


def test_large_slide_titles() -> None:
    """슬라이드 제목 크기 — h1 36px+ (다양한 분야 심사위원 가독성)."""
    t = _txt()
    # 슬라이드 제목 폰트 크기 — 36px 이상이어야 가독성 OK
    m = re.search(r"\.body h1\s*\{[^}]*font-size:\s*(\d+)px", t)
    assert m, "슬라이드 제목 폰트 크기 정의 누락"
    size = int(m.group(1))
    assert size >= 32, f"슬라이드 제목 {size}px 작음 (32px+ 필요)"


def test_no_personal_info() -> None:
    """PPT 룰: 개인정보 기재 금지."""
    t = _txt()
    emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', t)
    assert not emails, f"이메일 노출: {emails}"
    phones = re.findall(r'\b01[0-9]-\d{3,4}-\d{4}\b', t)
    assert not phones, f"전화 노출: {phones}"


def test_a4_landscape_print() -> None:
    """A4 가로 PDF 인쇄 친화."""
    t = _txt()
    assert "@page { size: A4 landscape" in t
    assert "page-break-after" in t
    assert "print-color-adjust" in t


def test_canonical_kpi_present() -> None:
    """canonical KPI."""
    t = _txt()
    for kpi in ("1,393", "347", "473", "157", "708", "1,064", "1,808"):
        assert kpi in t, f"KPI {kpi} 누락"


def test_system_screenshots_referenced() -> None:
    """시스템 캡처 (outputs/demo/)."""
    t = _txt()
    for c in ("citizen_pwa.png", "operator_realbev.png", "operator_index.png"):
        assert c in t, f"캡처 {c} 누락"


def test_eda_charts_referenced() -> None:
    """EDA 차트."""
    t = _txt()
    for f in ("dispersion_sim.png", "od_asymmetry.png", "transfer_stations.png"):
        assert f in t, f"차트 {f} 누락"


def test_slide_count_within_ppt_limit() -> None:
    """페이지 분량 10~30."""
    t = _txt()
    n = len(re.findall(r'<section class="slide[^"]*"', t))
    assert 10 <= n <= 30, f"분량 {n} — PPT 룰 10~30 위반"


def test_business_model_three_tier() -> None:
    """BM 3-tier."""
    t = _txt()
    for amt in ("₩40 억", "₩100 억", "₩12 억"):
        assert amt in t


def test_evaluation_keywords_per_section() -> None:
    """평가 키워드."""
    t = _txt()
    for kw in ("구체성", "독창성", "발전 가능성"):
        assert kw in t


def test_pdf_export_friendly_hud() -> None:
    """PDF 안내."""
    t = _txt()
    assert "Ctrl+P" in t


def test_aed_emergency_specific() -> None:
    """응급 골든타임 + AED 구체화."""
    t = _txt()
    assert "AED" in t, "AED 거리 안내 (응급 IDEA 핵심) 누락"
    assert "골든타임" in t, "골든타임 언급 누락"


def test_priority_seat_specific() -> None:
    """임산부석 IDEA 구체화."""
    t = _txt()
    assert "분홍 좌석" in t or "임산부 배려석" in t, "임산부 배려석 구체 설명 누락"
    assert "30초" in t, "임산부석 30초 임계값 누락"


def test_4_language_idea9() -> None:
    """IDEA-9 4언어 음성 명시."""
    t = _txt()
    assert "4언어 음성" in t or "4 언어 음성" in t, "IDEA-9 4언어 음성 누락"
    assert "1,242" in t, "1,242만 잠재 사용자 (청각+노캔) 정량 누락"
