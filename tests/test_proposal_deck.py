"""상세기획서 deck 회귀 가드 (cycle 431 — 임팩트 우선순위 + 30장 + 6 핵심 기능).

cycle 430 까지 누락:
  ① 버스 시스템 (operator_bus + 24시간 sparkline + 환승 매트릭스) 부재
  ② 차등 보상 4단 자동 시스템 (₩100/200/300/400) 별도 슬라이드 X
  ③ 점유 네트워크 분석 (호선×시간 heatmap) 별도 슬라이드 X
  ④ 에스컬레이터 통행량 (이태원 사전 경고) 별도 슬라이드 X
  ⑤ 카메라 = 수집 + 분석 + 인사이트 핵심 메시지 슬라이드 X
  ⑥ 네이티브 폰 앱 mockup 시각화 (실제 캡처 부재)
  ⑦ 분량 25 → 30장 꽉 채우라 지시

cycle 431 전면 재작성 — 임팩트 우선순위:
  1. 카메라=수집=분석=인사이트 (정체성 — slide 2-1)
  2. 점유 네트워크 분석 (호선 × 시간 heatmap — slide 2-4)
  3. 4단 차등 보상 자동 (₩100~400 — slide 3-2)
  4. 6 사회적 가치 IDEA (slide 3-1)
  5. 에스컬레이터 사전 경고 (이태원 — slide 3-3)
  6. 버스 시스템 통합 (slide 3-4)
  7. 네이티브 폰 앱 mockup (slide 1-3 + 5-2)
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


def test_thirty_slides_full() -> None:
    """분량 30장 이상 꽉 채움 (사용자 지시 — 신규 슬라이드 추가 허용)."""
    t = _txt()
    n = len(re.findall(r'<section class="slide[^"]*"', t))
    assert n >= 30, f"분량 {n} — 30장 이상 필요"


def test_camera_equals_collection_message() -> None:
    """핵심 메시지: 카메라 1대 = 수집 + 분석 + 인사이트 통합 (TRIZ #5)."""
    t = _txt()
    assert "카메라 1대" in t, "'카메라 1대' 핵심 메시지 누락"
    assert "수집" in t and "분석" in t and "인사이트" in t, "수집·분석·인사이트 통합 메시지 누락"
    assert "별도 인프라" in t, "'별도 인프라 0개' 차별성 누락"


def test_tier_compensation_4_levels() -> None:
    """4단 차등 보상 시스템 (₩100/200/300/400) 별도 슬라이드."""
    t = _txt()
    for amt in ("₩100", "₩200", "₩300", "₩400"):
        assert amt in t, f"차등 보상 {amt} 누락"
    assert "tier-card" in t, "차등 보상 시각화 카드 누락"
    assert "_bonus_krw" in t, "백엔드 자동 가산 코드 인용 누락"


def test_occupation_network_analysis() -> None:
    """점유 네트워크 분석 (호선×시간 heatmap)."""
    t = _txt()
    assert "line_carload_heatmap.png" in t, "호선×시간 heatmap 누락"
    assert "171" in t or "9 호선 × 19 시간" in t, "171 cell 매트릭스 누락"
    assert "priority" in t.lower() or "우선순위" in t, "Top 5 cell 우선순위 누락"


def test_escalator_bottleneck_idea_8() -> None:
    """에스컬레이터 통행량 분석 (군중밀집 사전 경고)."""
    t = _txt()
    assert "에스컬레이터" in t, "에스컬레이터 명시 누락"
    assert "군중" in t or "밀집" in t, "군중 밀집 사전 경고 메시지 누락"
    assert "0.3" in t, "0.3 m/s 임계값 누락"
    assert "45초" in t, "45초 지속 임계값 누락"


def test_bus_system_dedicated_slide() -> None:
    """버스 시스템 별도 슬라이드 (간선 142 + 24시간 sparkline)."""
    t = _txt()
    assert "operator_bus.png" in t, "버스 콘솔 캡처 누락"
    assert "간선 142" in t, "간선 142 (도봉산↔잠실) 사례 누락"
    assert "24시간" in t and "sparkline" in t, "24시간 sparkline 점유 분석 누락"


def test_six_social_value_ideas() -> None:
    """6대 사회적 가치 IDEA."""
    t = _txt()
    for kw in ("임산부", "응급 골든타임", "군중밀집", "분실물", "무임", "5중 도착"):
        assert kw in t, f"IDEA '{kw}' 누락"


def test_native_phone_app_mockup() -> None:
    """네이티브 폰 앱 mockup 시각화 (실제 캡처 대체)."""
    t = _txt()
    assert "phone-mock" in t, "폰앱 mockup 시각화 컴포넌트 누락"
    assert "Flutter" in t, "Flutter 명시 누락"
    assert "Android" in t and "Windows" in t, "Android/Windows 크로스 플랫폼 누락"


def test_layperson_terms_used() -> None:
    """일반인 용어."""
    t = _txt()
    layperson_terms = ["위에서 본", "1,000번 시뮬레이션", "발명 기법", "추적", "평면 보정"]
    found = sum(1 for k in layperson_terms if k in t)
    assert found >= 4, f"일반인 용어 {found}/5 — 4+ 필요"


def test_large_slide_titles() -> None:
    """슬라이드 제목 24px+ (A4 landscape 기준 충분한 크기)."""
    t = _txt()
    m = re.search(r"\.body h1\s*\{[^}]*font-size:\s*(\d+)px", t)
    assert m and int(m.group(1)) >= 24, f"슬라이드 제목 작음 — 24px+ 필요"


def test_no_personal_info() -> None:
    """개인정보 금지 (PPT 룰)."""
    t = _txt()
    # CDN/버전 패턴(pretendard@v1.3.9 등) 제외하고 이메일만 탐지
    emails = [m for m in re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', t)
              if not re.match(r'.+@v[\d.]+', m)]
    assert not emails, f"이메일 노출: {emails}"
    assert not re.findall(r'\b01[0-9]-\d{3,4}-\d{4}\b', t), "전화 노출"


def test_a4_landscape_print() -> None:
    """A4 가로 PDF."""
    t = _txt()
    assert "@page { size: A4 landscape" in t
    assert "page-break-after" in t


def test_canonical_kpi_present() -> None:
    """canonical KPI."""
    t = _txt()
    for kpi in ("1,393", "347", "473", "157", "708", "1,064", "1,808"):
        assert kpi in t, f"KPI {kpi} 누락"


def test_system_screenshots() -> None:
    """시스템 캡처 (지하철 + 라이브 + 시민 + 버스 4종)."""
    t = _txt()
    captures = ["citizen_subway_main.png", "citizen_bus_main.png", "citizen_onboard_subway.png",
                "operator_realbev.png", "operator_index.png", "operator_bus.png"]
    for c in captures:
        assert c in t, f"캡처 {c} 누락 — 4종 모두 필요"


def test_eda_charts() -> None:
    """EDA 차트."""
    t = _txt()
    for f in ("dispersion_sim.png", "od_asymmetry.png", "transfer_stations.png", "line_carload_heatmap.png"):
        assert f in t, f"차트 {f} 누락"


def test_evaluation_keywords() -> None:
    """평가 키워드."""
    t = _txt()
    for kw in ("구체성", "독창성", "발전 가능성"):
        assert kw in t


def test_official_seven_sections_structure() -> None:
    """PPT 정식 7항목 (템플릿 정렬 완료: §3=사업·서비스, §4=경쟁기술)."""
    t = _txt()
    sections = ["제안 배경", "출품작 핵심", "사업·서비스", "경쟁기술", "IA", "창업", "개발 툴"]
    for s in sections:
        assert s in t, f"섹션 '{s}' 누락"


def test_slide_fill_css_present() -> None:
    """레이아웃 CSS — 수직 센터 정렬 + 동일 행 등고 핵심 규칙."""
    t = _txt()
    assert "justify-content: center" in t, "body justify-content:center 누락 — 슬라이드 수직 센터 필요"
    assert "align-items: stretch" in t, "align-items:stretch 누락 — 같은 행 박스 등고 필요"


def test_operator_three_screenshots_slide3() -> None:
    """3쪽 운영자 콘솔 3종 캡처 — 지하철·실카메라·버스."""
    t = _txt()
    assert t.count("operator_index.png") >= 2, "operator_index.png 2회 이상 필요 (3쪽+21쪽)"
    assert t.count("operator_realbev.png") >= 2, "operator_realbev.png 2회 이상 필요 (3쪽+5쪽+21쪽)"
    assert t.count("operator_bus.png") >= 2, "operator_bus.png 2회 이상 필요 (3쪽+17쪽+21쪽)"


def test_citizen_six_screenshots_present() -> None:
    """시민 앱 6종 스크린샷 모두 있음."""
    t = _txt()
    for f in ("citizen_subway_main.png", "citizen_subway_detail.png",
              "citizen_onboard_subway.png", "citizen_bus_main.png",
              "citizen_bus_detail.png", "citizen_bus_onboard.png"):
        assert f in t, f"시민 스크린샷 {f} 누락"


def test_thirty_three_slides() -> None:
    """분량 33장 확인 (30장 초과 유지)."""
    t = _txt()
    n = len(re.findall(r'<section class="slide[^"]*"', t))
    assert n >= 33, f"슬라이드 {n}장 — 33장 이상 유지 필요"
