"""ESG CO₂ 절감 EDA 회귀 (cycle 390).

ultra-conservative (0.012 광고) ↔ standard (0.088 실효) 두 시나리오 동시 산출.
admin.html 광고 0.012 kg/action ↔ EDA derivation 일치 자동 검증.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "frontend" / "figs" / "co2_savings_report.json"


def _load() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_report_exists() -> None:
    assert REPORT.exists(), f"missing {REPORT} — run scripts/eda_co2_savings.py"


def test_advertised_0012_matches_ultra_derivation() -> None:
    """admin / pitch 광고 0.012 kg ↔ ultra-conservative derivation 일치."""
    d = _load()
    assert d["advertised_value_kg"] == 0.012, "advertised value 0.012 missing"
    assert d["match_advertised_ultra"] is True, \
        f"광고 0.012 vs ultra derivation 불일치: {d['co2_per_action_kg_ultra']}"


def test_two_scenarios_coexist() -> None:
    """ultra 와 standard 두 시나리오 모두 산출 (정직성 + 실효)."""
    d = _load()
    assert d["co2_per_action_kg_ultra"] == 0.012, f"ultra: {d['co2_per_action_kg_ultra']}"
    assert d["co2_per_action_kg_standard"] > 0.05, "standard derivation should be ≥0.05"
    assert d["co2_per_action_kg_standard"] / d["co2_per_action_kg_ultra"] > 5, \
        "standard 가 ultra의 5배 이상이어야 (광고 보수성 어필)"


def test_5_scenarios_each() -> None:
    """5 응답률 시나리오 (5/15/30/50/70%) 모두 ultra + standard 결과 보유."""
    d = _load()
    assert len(d["scenarios_ultra"]) == 5
    assert len(d["scenarios_standard"]) == 5
    rates = [s["response_rate"] for s in d["scenarios_ultra"]]
    assert rates == [0.05, 0.15, 0.30, 0.50, 0.70], f"unexpected rates: {rates}"


def test_30pct_ultra_scenario() -> None:
    """30% 시나리오 — ultra 약 2,800 톤 / standard 약 20,000 톤."""
    d = _load()
    sc30u = d["scenario_30pct_ultra"]
    sc30s = d["scenario_30pct_standard"]
    assert 2500 <= sc30u["co2_yr_t"] <= 3200, f"30% ultra t/yr unexpected: {sc30u['co2_yr_t']}"
    assert 18000 <= sc30s["co2_yr_t"] <= 23000, f"30% standard t/yr unexpected: {sc30s['co2_yr_t']}"


def test_sources_documented() -> None:
    """assumption 들의 출처 (한국교통연구원 / 서울교통공사 / 환경부) 명시."""
    d = _load()
    sources = d["sources"]
    assert "한국교통연구원" in sources["car_avoidance_std"], "한국교통연구원 출처 누락"
    assert "서울교통공사" in sources["commute_km"], "서울교통공사 출처 누락"
    assert "환경부" in sources["kg_co2_per_km"], "환경부 출처 누락"
