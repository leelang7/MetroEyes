"""MetroEyes 환승 부담 EDA 회귀 가드 (cycle 543).

CardSubwayTime 승하차 불균형 분석 로직 검증:
  1. 합성 데이터 생성 — 실 파일 없이 분리 실행 가능
  2. peak_on_off_by_station — 역별 부담 지수 정렬
  3. 고부담 역 분류 — threshold 1.2 이상
  4. metroeyes_roi_estimate — 연간 억원 ROI 추정
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from eda_transfer_burden import (
    TRANSFER_BURDEN_THRESHOLD,
    PEAK_HOURS,
    load_cardsubwaytime,
    peak_on_off_by_station,
    metroeyes_roi_estimate,
)


def _df():
    return load_cardsubwaytime()


def _ranked():
    return peak_on_off_by_station(_df())


def test_peak_hours_include_commute() -> None:
    """피크 시간대에 출퇴근 시간(7-9, 17-19) 포함."""
    assert 8 in PEAK_HOURS and 18 in PEAK_HOURS, "출퇴근 피크 시간대 포함 필요"


def test_threshold_positive() -> None:
    """환승 부담 임계값 양수."""
    assert TRANSFER_BURDEN_THRESHOLD > 0


def test_threshold_range() -> None:
    """임계값 1.0~2.0 합리적 범위."""
    assert 1.0 <= TRANSFER_BURDEN_THRESHOLD <= 2.0, "환승 부담 임계 1.0~2.0 범위 벗어남"


def test_synthetic_data_loads() -> None:
    """합성 데이터 로드 — 실 파일 없어도 동작."""
    df = _df()
    assert len(df) > 0, "데이터 로드 실패"


def test_synthetic_has_required_columns() -> None:
    """CardSubwayTime 필수 컬럼 존재."""
    df = _df()
    assert "SUB_STA_NM" in df.columns
    assert "LINE_NUM" in df.columns
    assert "HR_07_GET_ON_NOPE" in df.columns
    assert "HR_18_GET_OFF_NOPE" in df.columns


def test_ranked_returns_all_stations() -> None:
    """peak_on_off_by_station — 모든 역 반환."""
    df = _df()
    ranked = peak_on_off_by_station(df)
    stations_in = df["SUB_STA_NM"].nunique()
    assert len(ranked) == stations_in, "역 개수 불일치"


def test_ranked_sorted_descending() -> None:
    """전환 부담 지수 내림차순 정렬."""
    ranked = _ranked()
    burdens = list(ranked["transfer_burden"])
    assert burdens == sorted(burdens, reverse=True), "전환 부담 내림차순 정렬 오류"


def test_burden_positive() -> None:
    """모든 역 전환 부담 지수 양수."""
    ranked = _ranked()
    assert (ranked["transfer_burden"] > 0).all(), "음수 부담 지수 존재"


def test_high_burden_at_least_one() -> None:
    """고부담 역 최소 1개 이상 — MetroEyes 배치 근거."""
    ranked = _ranked()
    assert ranked["high_burden"].any(), "고부담 역 0개 — 임계값 확인 필요"


def test_roi_estimate_positive() -> None:
    """ROI 추정치 양수."""
    roi = metroeyes_roi_estimate(1000, 1.5)
    assert roi > 0, "ROI 추정치 음수"


def test_roi_scales_with_burden() -> None:
    """부담 지수 증가 → ROI 증가."""
    roi_low = metroeyes_roi_estimate(1000, 1.2)
    roi_high = metroeyes_roi_estimate(1000, 2.0)
    assert roi_high > roi_low, "부담 지수-ROI 단조 증가 관계 오류"


def test_roi_scales_with_volume() -> None:
    """승객 수 증가 → ROI 증가."""
    roi_small = metroeyes_roi_estimate(1000, 1.5)
    roi_large = metroeyes_roi_estimate(5000, 1.5)
    assert roi_large > roi_small, "승객 수-ROI 비례 관계 오류"
