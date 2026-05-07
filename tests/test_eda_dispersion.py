"""분산 효과 EDA 결과 회귀 — pitch.html 그림 1 / README KPI 광고 수치 가드.

frontend/figs/dispersion_sim_report.json 의 핵심 통계가 README/pitch에 광고된 값과 일치.
- σ −9.0% / 피크 −13.5% / 비피크 +5.6% / 피크/비피크 비율 1.78 → 1.46
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "frontend" / "figs" / "dispersion_sim_report.json"


def _load() -> dict:
    with REPORT.open(encoding="utf-8") as f:
        return json.load(f)


def test_report_exists() -> None:
    assert REPORT.exists(), f"missing {REPORT}"


def test_sigma_reduction_9pct() -> None:
    """σ 감소 −9.0% (광고: σ −9%)."""
    d = _load()
    s = d["sigma_reduction_pct"]
    assert -9.5 <= s <= -8.5, f"sigma_reduction_pct={s:.2f} — README says −9.0%"


def test_peak_reduction_13_5pct() -> None:
    """피크 평균 감소 −13.5% (광고: 피크 −13.5%)."""
    d = _load()
    p = d["peak_reduction_pct"]
    assert -14.0 <= p <= -13.0, f"peak_reduction_pct={p:.2f} — README says −13.5%"


def test_offpeak_lift_5_6pct() -> None:
    """비피크 +5.6% (광고: 비피크 +5.6%)."""
    d = _load()
    o = d["offpeak_lift_pct"]
    assert 5.0 <= o <= 6.2, f"offpeak_lift_pct={o:.2f} — README says +5.6%"


def test_peak_offpeak_ratio_178_to_146() -> None:
    """피크/비피크 비율 1.78 → 1.46 (광고: 1.78→1.46)."""
    d = _load()
    before = d["peak_offpeak_ratio_before"]
    after = d["peak_offpeak_ratio_after"]
    assert 1.75 <= before <= 1.81, f"ratio_before={before:.2f} — README says 1.78"
    assert 1.43 <= after <= 1.49, f"ratio_after={after:.2f} — README says 1.46"


def test_response_rate_30pct() -> None:
    """기본 시나리오 응답률 30%."""
    d = _load()
    assert d["response_rate"] == 0.30
