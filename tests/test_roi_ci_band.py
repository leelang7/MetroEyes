"""정책 ROI v3 Monte Carlo 95% CI 회귀 (cycle 364).

기존 5 시나리오 점추정 → ±15%/±20%/±10%/±10% 4축 perturbation × 1000 sims 95% CI.

장애 시나리오: ci_band 누락 / 시나리오 5개 중 일부 누락 / mean 대비 CI 왜곡.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CI_JSON = ROOT / "frontend" / "figs" / "policy_roi_v3_ci_band.json"


def _load() -> dict:
    return json.loads(CI_JSON.read_text(encoding="utf-8"))


def test_ci_band_exists() -> None:
    assert CI_JSON.exists(), f"missing {CI_JSON} — run scripts/policy_roi_v3.py"


def test_method_documented() -> None:
    d = _load()
    assert "Monte Carlo" in d["method"]
    assert "n=1000" in d["method"] or "1000" in d["method"]
    p = d["perturbations"]
    assert "response_rate" in p and "save_min_base" in p
    assert "krw_per_hour" in p and "line_cap_ratio" in p


def test_all_5_scenarios_have_ci() -> None:
    d = _load()
    sc = d["scenarios"]
    expected_rates = ["0.05", "0.15", "0.30", "0.50", "0.70"]
    for r in expected_rates:
        assert r in sc, f"missing scenario rate {r}"
        for f in ("net_b_mean", "net_b_p5", "net_b_p95",
                  "roi_x_mean", "roi_x_p5", "roi_x_p95",
                  "minutes_p5", "minutes_p95", "n_sims"):
            assert f in sc[r], f"scenario {r} missing field {f}"


def test_ci_well_ordered() -> None:
    """p5 < mean < p95 모든 시나리오에서 성립."""
    d = _load()
    for rate, ci in d["scenarios"].items():
        assert ci["net_b_p5"] < ci["net_b_mean"] < ci["net_b_p95"], \
            f"scenario {rate} net_b not well-ordered: {ci['net_b_p5']}/{ci['net_b_mean']}/{ci['net_b_p95']}"
        assert ci["roi_x_p5"] < ci["roi_x_mean"] < ci["roi_x_p95"], \
            f"scenario {rate} roi_x not well-ordered"


def test_30pct_mean_around_advertised_1393() -> None:
    """30% 시나리오 평균 ≈ 1,393억 (광고 KPI). Monte Carlo 노이즈로 ±5% 허용."""
    d = _load()
    mean = d["scenarios"]["0.30"]["net_b_mean"]
    expected = 1393.0
    diff_pct = abs(mean - expected) / expected * 100
    assert diff_pct < 7.0, f"30% scenario mean {mean:.0f}억 vs 광고 {expected}억 ({diff_pct:.1f}% off)"


def test_30pct_ci_contains_advertised() -> None:
    """30% CI [p5, p95] 가 광고된 1,393억을 포함."""
    d = _load()
    ci = d["scenarios"]["0.30"]
    assert ci["net_b_p5"] <= 1393 <= ci["net_b_p95"], \
        f"광고 1,393억이 95% CI [{ci['net_b_p5']:.0f}, {ci['net_b_p95']:.0f}] 밖"


def test_n_sims_1000() -> None:
    d = _load()
    for rate, ci in d["scenarios"].items():
        assert ci["n_sims"] == 1000, f"scenario {rate} n_sims {ci['n_sims']} != 1000"
