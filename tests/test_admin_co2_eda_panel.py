"""admin.html ESG CO₂ EDA 라이브 패널 회귀 (cycle 391).

cycle 390 의 co2_savings_report.json 을 admin.html ESG 패널이 자동 fetch →
ultra/standard 30% 시나리오 톤/년 라이브 표시.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADMIN = ROOT / "frontend" / "admin.html"
REPORT = ROOT / "frontend" / "figs" / "co2_savings_report.json"


def _admin() -> str:
    return ADMIN.read_text(encoding="utf-8")


def test_panel_dom_present() -> None:
    """ESG CO₂ EDA 카드 DOM 존재 (loadCO2EDA + esg-co2-30pct)."""
    html = _admin()
    assert 'id="esg-co2-eda"' in html, "ESG CO2 EDA card missing"
    assert 'id="esg-co2-30pct"' in html, "30% scenario container missing"
    assert "loadCO2EDA" in html, "loader function missing"
    assert "fetch('figs/co2_savings_report.json'" in html, "report fetch missing"


def test_two_scenarios_displayed() -> None:
    """ultra / standard 두 시나리오 모두 표시 (cycle 390 정직성)."""
    html = _admin()
    assert "ultra" in html and "standard" in html, "two scenarios not labeled"
    # 0.012 / 5% 양쪽 derivation 명시
    assert "0.7%" in html and "0.012" in html, "ultra 0.7% derivation missing"
    assert "5%" in html, "standard 5% derivation missing"
    # 7배 (실효 vs 광고) 명시
    assert "7배" in html, "7x ratio (실효 vs 광고) missing"


def test_committed_report_still_present() -> None:
    """cycle 390 결과 JSON 이 admin 이 의존하는 경로에 그대로 있음."""
    assert REPORT.exists(), f"missing {REPORT} — cycle 390 결과 사라짐"
    d = json.loads(REPORT.read_text(encoding="utf-8"))
    assert "scenario_30pct_ultra" in d
    assert "scenario_30pct_standard" in d


def test_safe_fail_on_static_host() -> None:
    """fetch 실패 시 (정적 호스팅) catch 로 조용히 종료."""
    html = _admin()
    assert "} catch (e)" in html or "} catch {" in html, "fetch catch missing"
