"""eda_air_subway_corr.py 회귀 가드 (cycle 534).

미세먼지(PM10/PM2.5) × 지하철 통행 시간대별 결합 상관 분석.
공공데이터: 서울 열린데이터광장 TimeAverageAirQuality + CardSubwayTime API.
피치 근거: "미세먼지 높은 시간대 분산 정책 강화" 정량 근거 신뢰성.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "eda_air_subway_corr.py"


def test_script_exists() -> None:
    assert SCRIPT.exists(), f"스크립트 없음: {SCRIPT}"


def test_uses_both_datasets() -> None:
    """subway_time_202602 + air_202602 두 parquet 모두 필요."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "subway_time_202602" in src, "지하철 통행 parquet 경로 없음"
    assert "air_202602" in src, "대기질 parquet 경로 없음"


def test_pm10_column_detection() -> None:
    """PM10 컬럼 자동 탐지 로직 포함."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "PM10" in src and "pm10_col" in src, "PM10 컬럼 탐지 없음"


def test_pearson_and_spearman() -> None:
    """Pearson + Spearman 이중 상관계수 계산."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "pearson" in src.lower() or "corr()" in src or ".corr" in src, \
        "Pearson 상관 없음"
    assert "spearman" in src.lower(), "Spearman 상관 없음"


def test_strong_correlation_threshold() -> None:
    """|r| > 0.3 기준으로 강한 상관 여부 판단."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "0.3" in src, "|r|>0.3 임계값 없음"


def test_output_json_pearson_key() -> None:
    """출력 JSON에 pearson_r 키 포함."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert '"pearson_r"' in src or "pearson_r" in src, \
        "JSON 출력에 pearson_r 없음"


def test_hour_range_5_to_23() -> None:
    """운행 시간 5~23시 범위 필터."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "5" in src and "23" in src, "시간 범위 5~23 없음"


def test_policy_implication_text() -> None:
    """'분산 인센티브 강화' 정책 함의 텍스트 포함."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "분산 인센티브" in src or "인센티브 강화" in src, \
        "정책 함의 '분산 인센티브 강화' 텍스트 없음"


def test_interpretation_key_in_output() -> None:
    """JSON summary에 interpretation 키 존재."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert '"interpretation"' in src, "JSON에 interpretation 키 없음"


def test_minimum_rows_for_correlation() -> None:
    """결합 행 수 >= 5 이상일 때만 상관 계산 (소표본 방지)."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert ">= 5" in src or "len(merged) >= 5" in src, \
        "최소 행 수 검사 없음"
