"""KPI drift 자동 감지 (cycle 375) — 광고-코드 자동 정합 시스템.

cycle 374 사고 (광고 157M ↔ EDA 138M 충돌이 D-5 까지 미발견) 재발 방지:
canonical KPI (frontend/figs/policy_roi_v3_canonical_kpi.json) 가 진실의 원천.
모든 광고 자료 (pitch / onepager / demo / PROPOSAL / SLIDES / narration)
가 이 값을 그대로 광고하는지 자동 검증.

policy_roi_v3.py 실행 → canonical 갱신 → 광고 자료 동기화 안 한 경우 즉시 fail.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANONICAL = ROOT / "frontend" / "figs" / "policy_roi_v3_canonical_kpi.json"


def _load() -> dict:
    return json.loads(CANONICAL.read_text(encoding="utf-8"))


def _read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.exists() else ""


def test_canonical_exists() -> None:
    assert CANONICAL.exists(), \
        f"missing {CANONICAL} — run scripts/policy_roi_v3.py to regenerate"


def test_canonical_schema() -> None:
    d = _load()
    s = d["scenario_30pct"]
    for k in ("net_value_b", "roi_x", "minutes_saved_yr_m", "infra_b", "n_stations_priority"):
        assert k in s, f"canonical scenario_30pct missing {k}"
    assert "per_line_saved_min_m" in d
    assert "ci_30pct" in d


def test_advertised_net_value_consistent() -> None:
    """1,393억 (canonical) ↔ pitch / onepager / SLIDES / PROPOSAL / README 동시 일치."""
    d = _load()
    net_b = d["scenario_30pct"]["net_value_b"]
    needle = f"{net_b:,}억"  # "1,393억"
    for f in ("frontend/pitch.html", "frontend/onepager.html",
              "docs/PROPOSAL.md", "docs/SLIDES_DECK.md", "docs/SLIDES.html",
              "README.md"):
        body = _read(f)
        assert needle in body, f"{f} missing canonical net_value '{needle}'"


def test_advertised_roi_consistent() -> None:
    """ROI 347x ↔ 모든 광고 자료 동시 일치."""
    d = _load()
    roi = d["scenario_30pct"]["roi_x"]
    pattern1 = f"{roi}x"
    pattern2 = f"{roi}배"
    pattern3 = f"{roi}<"   # SLIDES.html 의 "347<span class=...>×"
    for f in ("frontend/pitch.html", "frontend/onepager.html",
              "docs/PROPOSAL.md", "docs/SLIDES_DECK.md", "docs/SLIDES.html",
              "README.md"):
        body = _read(f)
        assert (pattern1 in body or pattern2 in body or pattern3 in body), \
            f"{f} missing canonical ROI '{pattern1}/{pattern2}/{pattern3}'"


def test_2hosun_saved_min_consistent() -> None:
    """2호선 saved_min (canonical 157.3M) ↔ 광고 '157M' 일치 — cycle 374 회귀 방지."""
    d = _load()
    line2_m = d["per_line_saved_min_m"]["2호선"]
    rounded = round(line2_m)  # 157
    # 광고는 정수로 "157M" 으로 쓰임
    needle = f"{rounded}M"
    for f in ("frontend/pitch.html", "frontend/onepager.html", "frontend/demo.html",
              "docs/PROPOSAL.md", "docs/SLIDES_DECK.md", "docs/SLIDES.html",
              "docs/RECORDING_NARRATION.md", "README.md"):
        body = _read(f)
        assert needle in body, \
            f"{f} missing 2호선 saved_min '{needle}' (canonical {line2_m}M)"


def test_ci_band_30pct_advertised() -> None:
    """30% Monte Carlo CI [p5, p95] ↔ pitch / SLIDES / PROPOSAL / onepager 동시 일치."""
    d = _load()
    p5 = d["ci_30pct"]["net_b_p5"]
    p95 = d["ci_30pct"]["net_b_p95"]
    p5s = f"{p5:,}"  # "1,064"
    p95s = f"{p95:,}"  # "1,808"
    for f in ("frontend/pitch.html", "frontend/onepager.html",
              "docs/PROPOSAL.md", "docs/SLIDES_DECK.md", "docs/SLIDES.html"):
        body = _read(f)
        assert p5s in body, f"{f} missing CI p5 '{p5s}'"
        assert p95s in body, f"{f} missing CI p95 '{p95s}'"
