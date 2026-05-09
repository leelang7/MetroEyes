"""상세기획서 30 슬라이드 HTML 회귀 가드 (cycle 428).

docs/proposal_deck.html — 2026 서울시 빅데이터 활용 경진대회 (창업 부문) 상세기획서 PPT 대체.
PDF 인쇄 친화 (@page A4 landscape) · 30 슬라이드 · 사진/도표 풍부.
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


def test_thirty_slides() -> None:
    """정확히 30 슬라이드 (<section class=\"slide\"...>)."""
    t = _txt()
    n = len(re.findall(r'<section class="slide[^"]*"', t))
    assert n == 30, f"expected 30 slides, got {n}"


def test_a4_landscape_print() -> None:
    """@page A4 landscape + PDF 인쇄 친화."""
    t = _txt()
    assert "@page { size: A4 landscape" in t, "A4 landscape @page rule 누락"
    assert "page-break-after" in t, "page-break-after 누락 (PDF 변환 시 페이지 분할 안 됨)"
    assert "print-color-adjust" in t, "print-color-adjust (배경 그래픽 인쇄) 누락"


def test_canonical_kpi_present() -> None:
    """canonical KPI 4 종 모두 deck 안에 (drift 차단)."""
    t = _txt()
    for kpi in ("1,393", "347", "473.4", "157", "708", "1,064", "1,808"):
        assert kpi in t, f"canonical KPI {kpi} 누락 — drift 위험"


def test_charts_referenced() -> None:
    """frontend/figs PNG 5종 이상 deck 안에 (사진/도표 풍부 요건)."""
    t = _txt()
    figs = [
        "dispersion_sim.png",
        "od_asymmetry.png",
        "transfer_stations.png",
        "policy_roi_v3_per_line.png",
        "line_carload_heatmap.png",
    ]
    for f in figs:
        assert f in t, f"chart {f} 참조 누락"


def test_business_model_three_tier() -> None:
    """비즈니스 모델 3-tier (B2G + B2B 광고 + B2B Data) 모두."""
    t = _txt()
    for kw in ("B2G", "B2B 광고", "B2B Data"):
        assert kw in t, f"BM tier {kw} 누락"
    for amt in ("₩40 억", "₩100 억", "₩12 억"):
        assert amt in t, f"BM 매출 {amt} 누락"


def test_evaluation_self_score_205() -> None:
    """1차 105 + 2차 100 = 205 자기 채점 + ESG 5축."""
    t = _txt()
    assert "105" in t and "100" in t and "205" in t, "1차 105 + 2차 100 = 205 누락"
    assert "ESG" in t, "ESG 5축 누락"


def test_rich_data_tables() -> None:
    """데이터 표 20+ (도표 풍부 요건)."""
    t = _txt()
    n = len(re.findall(r"<table>", t))
    assert n >= 20, f"expected 20+ tables, got {n} (도표 풍부 미충족)"


def test_pdf_export_friendly_hud() -> None:
    """화면 모드 HUD — Ctrl+P PDF 안내."""
    t = _txt()
    assert "Ctrl+P" in t or "PDF" in t, "PDF export 안내 누락"
