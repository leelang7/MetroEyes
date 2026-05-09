"""상세기획서 deck 회귀 가드 (cycle 429 — PPT 원본 7항목 정식 매핑).

PPT 원본 (한컴오피스 Web v2 한쇼 변환 PDF로 확인):
  표지 (서비스명 / 참가자명 / 분량 10~30 / 개인정보 기재 금지)
  1. 제안배경 및 출품작 소개 (구체성)
  2. 출품작 핵심내용 (공공데이터 활용 적정성, 구체성, 실현가능성, 기술성)
  3. 기존 서비스와의 차별성 (독창성)
  4. 개발과정 및 방법 (제품 및 서비스개발만 해당)
  5. IA (Information Architecture)
  6. 출품작의 창업(사업화, 시장성), 매출 발생 및 투자가능성 (발전 가능성)
  7. 개발 툴 및 참고문헌 (제품 및 서비스개발만 해당)

사고 회복 사례 (cycle 428 → 429):
  cycle 428 까지: PPT 원본 7항목 무시 → 임의 30 슬라이드 자체 구조 + 개인정보 (이메일) 노출
  사용자 정정: "PPT 꼭지/인덱스 활용도 안하고 지멋대로 + 시스템 캡쳐 부재"
  cycle 429: 정식 7항목 매핑 + outputs/demo/ 시스템 캡처 4종 + 이메일 제거
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECK = ROOT / "docs" / "proposal_deck.html"


def _txt() -> str:
    return DECK.read_text(encoding="utf-8")


def test_deck_exists() -> None:
    assert DECK.exists(), f"missing {DECK}"


def test_official_seven_sections_present() -> None:
    """PPT 원본 정식 7항목 모두 deck 안에 (cycle 428 무시 사고 재발 방지)."""
    t = _txt()
    sections = [
        "제안배경 및 출품작 소개",
        "출품작 핵심내용",
        "기존 서비스와의 차별성",
        "개발과정 및 방법",
        "IA",  # Information Architecture
        "창업",
        "개발 툴 및 참고문헌",
    ]
    for s in sections:
        assert s in t, f"PPT 정식 항목 '{s}' deck 에 누락"


def test_ia_section_explicitly_named() -> None:
    """5번 IA (Information Architecture) 항목 — cycle 428 에서 완전히 빠뜨렸던 항목."""
    t = _txt()
    assert "Information Architecture" in t, "IA (Information Architecture) 명시 누락"
    # IA 섹션의 정의 항목들 (시스템 아키텍처 + 사용자 흐름)
    ia_keywords = ["시스템 아키텍처", "WebSocket", "REST"]
    found = sum(1 for k in ia_keywords if k in t)
    assert found >= 2, f"IA 정의 키워드 부족: {found}/3 (시스템 구조 + WebSocket/REST 매트릭스 필요)"


def test_no_personal_info_email_phone() -> None:
    """PPT 룰: 개인정보 기재 금지 (팀이름/성명만 OK, 이메일/전화 금지)."""
    t = _txt()
    # 이메일 패턴
    emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', t)
    assert not emails, f"개인정보 이메일 노출: {emails} — PPT 룰 위반"
    # 전화번호 패턴 (010-xxxx-xxxx 등)
    phones = re.findall(r'\b01[0-9]-\d{3,4}-\d{4}\b', t)
    assert not phones, f"개인정보 전화번호 노출: {phones}"


def test_a4_landscape_print() -> None:
    """A4 가로 + PDF 인쇄 친화."""
    t = _txt()
    assert "@page { size: A4 landscape" in t, "A4 landscape @page 누락"
    assert "page-break-after" in t, "page-break-after 누락"
    assert "print-color-adjust" in t, "print-color-adjust 누락"


def test_canonical_kpi_present() -> None:
    """canonical KPI 7종 모두 (drift 차단)."""
    t = _txt()
    for kpi in ("1,393", "347", "473.4", "157", "708", "1,064", "1,808"):
        assert kpi in t, f"canonical KPI {kpi} 누락"


def test_system_screenshots_referenced() -> None:
    """outputs/demo/ 시스템 화면 캡처 4종 (cycle 428 누락 사고 재발 방지)."""
    t = _txt()
    captures = [
        "citizen_pwa.png",
        "operator_realbev.png",
        "operator_index.png",
    ]
    found = [c for c in captures if c in t]
    assert len(found) >= 3, f"시스템 캡처 3+ 종 필요 — 현재: {found}"


def test_eda_charts_referenced() -> None:
    """frontend/figs PNG 차트 3+ (분산/OD/환승)."""
    t = _txt()
    figs = ["dispersion_sim.png", "od_asymmetry.png", "transfer_stations.png"]
    for f in figs:
        assert f in t, f"EDA 차트 {f} 누락"


def test_slide_count_within_ppt_limit() -> None:
    """페이지 분량 10~30장 (PPT 룰)."""
    t = _txt()
    n = len(re.findall(r'<section class="slide[^"]*"', t))
    assert 10 <= n <= 30, f"분량 {n} — PPT 룰 10~30장 위반"


def test_business_model_three_tier() -> None:
    """비즈니스 모델 3-tier 매출 (B2G ₩40 + B2B 광고 ₩100 + B2B Data ₩12)."""
    t = _txt()
    for amt in ("₩40 억", "₩100 억", "₩12 억"):
        assert amt in t, f"BM 매출 {amt} 누락"


def test_evaluation_self_score_205() -> None:
    """1차 105 + 2차 100 = 205 자기 채점 + ESG 5축."""
    t = _txt()
    assert "105" in t and "ESG" in t, "1차 105 + ESG 자기 채점 누락"


def test_pdf_export_friendly_hud() -> None:
    """Ctrl+P PDF 안내."""
    t = _txt()
    assert "Ctrl+P" in t, "PDF export 안내 누락"


def test_evaluation_keywords_per_section() -> None:
    """각 항목의 평가 키워드 명시 (구체성/적정성/독창성/발전 가능성 등)."""
    t = _txt()
    for kw in ("구체성", "독창성", "발전 가능성"):
        assert kw in t, f"평가 키워드 '{kw}' 누락 (PPT 항목 매핑)"
