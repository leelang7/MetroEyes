"""MetroEyes 우선 설치 역 선정 EDA 회귀 가드 (cycle 541).

4 공공데이터 융합 로직 검증:
  1. compute_priority_score — 종합 점수 정렬 / 범위 / 가중치
  2. _normalize — [0,1] 범위 변환
  3. TOP10 구조 — rank/station/priority_score/capex_payback
  4. CapEx 단위경제 — 3,000만원 이하 / 회수 기간 양수
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from eda_priority_stations import (
    STATION_DATA,
    LINE_ROI_COEFF,
    CAPEX_PER_STATION_KRW,
    _normalize,
    compute_priority_score,
)


def test_station_data_not_empty() -> None:
    assert len(STATION_DATA) >= 10, "역 데이터 최소 10개 필요"


def test_line_roi_coeff_line2_highest() -> None:
    """2호선 ROI 계수 최고 — 708x 정책 근거."""
    assert LINE_ROI_COEFF["2호선"] == max(LINE_ROI_COEFF.values()), "2호선 ROI 계수 최고여야 함"


def test_normalize_range() -> None:
    """정규화 결과 [0, 1] 범위."""
    vals = [10, 20, 30, 40, 50]
    normed = _normalize(vals)
    assert min(normed) == pytest.approx(0.0, abs=1e-9)
    assert max(normed) == pytest.approx(1.0, abs=1e-9)


def test_normalize_single_value() -> None:
    """단일 값 정규화 시 0으로 처리 (ZeroDivision 방지)."""
    normed = _normalize([100])
    assert normed == [0.0]


def test_priority_score_returns_list() -> None:
    ranked = compute_priority_score(STATION_DATA)
    assert isinstance(ranked, list)
    assert len(ranked) == len(STATION_DATA)


def test_priority_score_sorted_descending() -> None:
    """점수 내림차순 정렬."""
    ranked = compute_priority_score(STATION_DATA)
    scores = [r["priority_score"] for r in ranked]
    assert scores == sorted(scores, reverse=True), "종합 점수 내림차순 정렬 오류"


def test_priority_score_range() -> None:
    """종합 점수 [0, 1] 범위."""
    ranked = compute_priority_score(STATION_DATA)
    for r in ranked:
        assert 0.0 <= r["priority_score"] <= 1.0, f"점수 범위 오류: {r}"


def test_rank_field_sequential() -> None:
    """rank 필드 1부터 순차."""
    ranked = compute_priority_score(STATION_DATA)
    for i, r in enumerate(ranked, 1):
        assert r["rank"] == i, f"rank 순번 오류: 기대 {i}, 실제 {r['rank']}"


def test_top1_is_line2() -> None:
    """1순위 역은 2호선 (ROI 최고 + 최고 밀도 조합)."""
    ranked = compute_priority_score(STATION_DATA)
    assert ranked[0]["line"] == "2호선", f"1순위 역 호선 오류: {ranked[0]}"


def test_capex_payback_positive() -> None:
    """모든 역 capex_payback_months 양수."""
    ranked = compute_priority_score(STATION_DATA)
    for r in ranked:
        assert r["capex_payback_months"] > 0, f"음수 회수 기간: {r}"


def test_monthly_riders_saved_positive() -> None:
    """월간 절감 승객수 양수."""
    ranked = compute_priority_score(STATION_DATA)
    for r in ranked:
        assert r["monthly_riders_saved"] > 0, f"월간 절감 승객수 0 이하: {r}"


def test_capex_per_station_300만() -> None:
    """역당 CapEx 300만원 — 단위경제 슬라이드 근거."""
    assert CAPEX_PER_STATION_KRW == 3_000_000, "역당 CapEx 300만원 정합"


def test_top10_all_required_keys() -> None:
    """TOP10 출력 필드 완전성."""
    ranked = compute_priority_score(STATION_DATA)
    required = {"rank", "station", "line", "daily_boarding", "od_asymmetry",
                "transfer_lines", "roi_coeff", "priority_score",
                "monthly_riders_saved", "capex_payback_months"}
    for r in ranked[:10]:
        missing = required - set(r.keys())
        assert not missing, f"필드 누락: {missing} in {r['station']}"
