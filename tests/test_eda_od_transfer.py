"""OD 비대칭 + 환승 비대칭 EDA 회귀 — pitch.html 그림 4/5 광고 수치 가드.

- OD: 삼성(무역센터) 출근 도착 OFF/ON 12.4x ★ README 광고
- 환승: 충무로 +1.56 / 연신내 +1.44 ★ README 광고
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OD = ROOT / "frontend" / "figs" / "od_asymmetry_report.json"
TR = ROOT / "frontend" / "figs" / "transfer_stations_report.json"


def _load_od() -> dict:
    with OD.open(encoding="utf-8") as f:
        return json.load(f)


def _load_tr() -> dict:
    with TR.open(encoding="utf-8") as f:
        return json.load(f)


def test_od_report_exists() -> None:
    assert OD.exists(), f"missing {OD}"


def test_tr_report_exists() -> None:
    assert TR.exists(), f"missing {TR}"


def test_od_samsung_top_arrival() -> None:
    """삼성(무역센터)가 top_arrival 1위 (출근 OFF/ON 비대칭 1위) — README 12.4x 근거."""
    d = _load_od()
    arrivals = d["top_arrival"]
    assert arrivals, "top_arrival empty"
    top = arrivals[0]
    # 삼성이 1위 또는 적어도 top 3 안에 있어야 함
    top3_names = [a["station"] for a in arrivals[:3]]
    assert any("삼성" in n for n in top3_names), f"삼성 not in top3 arrivals: {top3_names}"
    # OFF/ON 비율 (asym=0.85 → off/on = (1+0.85)/(1-0.85) ≈ 12.3 ✓)
    samsung = next((a for a in arrivals if "삼성" in a["station"]), None)
    if samsung:
        ratio = samsung["off"] / samsung["on"] if samsung["on"] > 0 else 0
        assert ratio >= 8, f"삼성 OFF/ON ratio={ratio:.1f} — README says 12.4x"


def test_tr_chungmuro_top_diff() -> None:
    """충무로가 top_am_diff 1위 (호선 간 비대칭 차이 +1.56) — README 광고."""
    d = _load_tr()
    am = d["top_am_diff"]
    assert am, "top_am_diff empty"
    top = am[0]
    assert top["station"] == "충무로", f"top am_diff station={top['station']} — README says 충무로"
    diff = top["diff"]
    assert 1.50 <= diff <= 1.62, f"충무로 diff={diff:.2f} — README says +1.56"


def test_tr_yeonsinnae_top_pm_diff() -> None:
    """연신내가 top_pm_diff 상위 (호선 간 비대칭 +1.44) — README 광고."""
    d = _load_tr()
    pm = d["top_pm_diff"]
    assert pm, "top_pm_diff empty"
    top3_names = [t["station"] for t in pm[:3]]
    assert "연신내" in top3_names, f"연신내 not in top3 pm_diff: {top3_names}"
    yeonsinnae = next((t for t in pm if t["station"] == "연신내"), None)
    if yeonsinnae:
        diff = yeonsinnae["diff"]
        assert 1.30 <= diff <= 1.55, f"연신내 diff={diff:.2f} — README says +1.44"


def test_od_am_pm_hours_canonical() -> None:
    """am_hour=9, pm_hour=19 — README OD AM/PM 자동 매칭 시간 일관성."""
    d = _load_od()
    assert d["am_hour"] in (8, 9, 10), f"am_hour={d['am_hour']} should be 8-10"
    assert d["pm_hour"] in (18, 19, 20), f"pm_hour={d['pm_hour']} should be 18-20"
