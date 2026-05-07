"""docs/FORM_DATA.md 마이박스 양식 사전 작성 데이터 회귀 (cycle 401).

D-day 사용자가 한컴 양식 4종 작성 시 copy-paste 즉시 활용 가능한 데이터 보유.
canonical KPI 모두 cross-reference + 9 공공데이터 양식 형식 정확히.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORM = ROOT / "docs" / "FORM_DATA.md"


def _txt() -> str:
    return FORM.read_text(encoding="utf-8")


def test_form_data_exists() -> None:
    assert FORM.exists(), f"missing {FORM}"


def test_4_forms_documented() -> None:
    """4종 양식 (참가신청서 / 동의서 / 사회조사서 / 상세기획서) 모두 명시."""
    t = _txt()
    for f in ("참가신청서", "개인정보 수집", "사회조사서", "상세기획서"):
        assert f in t, f"missing form: {f}"


def test_canonical_kpi_present() -> None:
    """핵심 KPI (cycle 374 정합) 모두 form data 안에."""
    t = _txt()
    for kpi in ("1,393억", "347x", "473.4M", "157M", "708x"):
        assert kpi in t, f"missing canonical KPI: {kpi}"


def test_9_public_apis_listed() -> None:
    """양식 형식 (`서울 열린데이터광장 - X`) 9 데이터셋 모두."""
    t = _txt()
    for ds in ("CardSubwayTime", "realtimeStationArrival", "citydata",
               "citydata_ppltn", "ListPublicReservationCulture",
               "TimeAverageAirQuality", "CardSubwayStatsNew"):
        assert ds in t, f"missing API dataset: {ds}"
    # 공공데이터포털 2개
    assert "버스정류소" in t, "bus stop dataset missing"
    assert "버스 노선" in t or "버스노선" in t, "bus route dataset missing"


def test_esg_5axes_documented() -> None:
    """ESG 5 축 (ENV / SOC / JOB / CO / GOV) 모두 form data 안에."""
    t = _txt()
    for axis in ("ENV", "SOC", "JOB", "CO", "GOV"):
        assert axis in t, f"missing ESG axis: {axis}"


def test_4_city_comparison_present() -> None:
    """차별성 표 — London / Tokyo / Singapore / MetroEyes 4 비교."""
    t = _txt()
    for city in ("London", "Tokyo", "Singapore", "MetroEyes"):
        assert city in t, f"missing comparison city: {city}"


def test_dday_checklist_present() -> None:
    """D-Day 제출 체크리스트 + submission_check.py 명령 명시."""
    t = _txt()
    assert "D-Day 5/13 18:00" in t or "D-Day" in t, "D-day deadline missing"
    assert "submission_check.py" in t, "submission_check command missing"
    assert "이상철_" in t, "naming convention 이상철_X 누락"


def test_one_line_pitch_present() -> None:
    """한 줄 자기 소개 (양식 공통)."""
    t = _txt()
    assert "Monte Carlo" in t and "708x" in t, "한 줄 pitch 누락"
