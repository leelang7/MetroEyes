"""eda_weekly_pattern.py 회귀 가드 (cycle 537).

요일별(주중/주말) 탑승 패턴 분석 — 가설 ⑥ 양봉/단봉 정량화.
공공데이터: 서울 열린데이터광장 CardSubwayTime 202602.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "eda_weekly_pattern.py"

sys.path.insert(0, str(ROOT / "scripts"))


def test_script_exists() -> None:
    assert SCRIPT.exists(), f"스크립트 없음: {SCRIPT}"


def test_month_constant_202602() -> None:
    src = SCRIPT.read_text(encoding="utf-8")
    assert '"202602"' in src or "'202602'" in src, "MONTH 202602 없음"


def test_weekday_weekend_constants() -> None:
    """주중(1~5) / 주말(6~7) 상수 정의."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "WEEKDAYS" in src, "WEEKDAYS 상수 없음"
    assert "WEEKENDS" in src, "WEEKENDS 상수 없음"


def test_peak_am_hours_defined() -> None:
    """오전 피크 시간대 7,8,9 정의."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "PEAK_AM_HOURS" in src, "PEAK_AM_HOURS 없음"
    assert "7, 8, 9" in src or "[7, 8, 9]" in src, "AM 피크 7-9 없음"


def test_peak_pm_hours_defined() -> None:
    """오후 피크 시간대 17,18,19 정의."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "PEAK_PM_HOURS" in src, "PEAK_PM_HOURS 없음"
    assert "17, 18, 19" in src or "[17, 18, 19]" in src, "PM 피크 17-19 없음"


def test_weekday_hourly_profile_function() -> None:
    """weekday_hourly_profile() 함수 존재."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "weekday_hourly_profile" in src, "weekday_hourly_profile 함수 없음"


def test_peak_ratio_function() -> None:
    """peak_ratio() 함수 존재."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "peak_ratio" in src, "peak_ratio 함수 없음"


def test_weekend_noon_ratio_function() -> None:
    """weekend_noon_ratio() 주말 단봉 지표 함수."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "weekend_noon_ratio" in src, "weekend_noon_ratio 함수 없음"


def test_bimodal_score_in_output() -> None:
    """bimodal_score 키 JSON 출력."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "bimodal_score" in src, "bimodal_score 출력 없음"


def test_hypothesis_6_label() -> None:
    """가설 ⑥ 레이블 포함."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "가설" in src and ("⑥" in src or "6" in src), "가설 ⑥ 레이블 없음"


def test_output_json_path() -> None:
    """weekly_pattern_summary.json 출력 경로."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "weekly_pattern_summary" in src, "출력 JSON 경로 없음"


def test_weekday_profile_returns_two_keys() -> None:
    """weekday_hourly_profile — weekday/weekend 2개 키 반환."""
    from eda_weekly_pattern import load_cardsubwaytime, weekday_hourly_profile
    df = load_cardsubwaytime("202602")
    profiles = weekday_hourly_profile(df)
    assert "weekday" in profiles, "weekday 키 없음"
    assert "weekend" in profiles, "weekend 키 없음"


def test_profile_length_24() -> None:
    """각 프로필 길이 24 (시간대)."""
    from eda_weekly_pattern import load_cardsubwaytime, weekday_hourly_profile
    df = load_cardsubwaytime("202602")
    profiles = weekday_hourly_profile(df)
    for key, vals in profiles.items():
        assert len(vals) == 24, f"{key} 프로필 길이 {len(vals)} ≠ 24"


def test_peak_ratio_bimodal_weekday() -> None:
    """주중 bimodal_score > 1.0 (피크 존재)."""
    from eda_weekly_pattern import load_cardsubwaytime, weekday_hourly_profile, peak_ratio
    df = load_cardsubwaytime("202602")
    profiles = weekday_hourly_profile(df)
    ratios = peak_ratio(profiles["weekday"])
    assert ratios["bimodal_score"] > 1.0, f"주중 bimodal_score 너무 낮음: {ratios['bimodal_score']}"


def test_weekend_noon_ratio_positive() -> None:
    """주말 정오 집중도 > 0."""
    from eda_weekly_pattern import load_cardsubwaytime, weekday_hourly_profile, weekend_noon_ratio
    df = load_cardsubwaytime("202602")
    profiles = weekday_hourly_profile(df)
    ratio = weekend_noon_ratio(profiles.get("weekend", [0.0] * 24))
    assert ratio > 0, f"주말 정오 집중도 0: {ratio}"
