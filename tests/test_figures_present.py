"""pitch.html이 참조하는 모든 figs/*.png 존재 + 비어있지 않음 검증.

pitch.html의 <img src="figs/X.png"> 가 빌드/배포 후 깨지지 않도록 가드.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PITCH = ROOT / "frontend" / "pitch.html"
FIGS_DIR = ROOT / "frontend" / "figs"


def test_pitch_exists() -> None:
    assert PITCH.exists() and PITCH.stat().st_size > 0


def test_all_referenced_figs_exist() -> None:
    """pitch.html이 <img src='figs/X.png'>로 참조하는 모든 파일이 figs/ 안에 비어있지 않게 존재."""
    html = PITCH.read_text(encoding="utf-8")
    refs = re.findall(r'<img\s[^>]*src="figs/([^"]+)"', html)
    assert refs, "no figs/* image references found in pitch.html"
    missing = []
    empty = []
    for fname in set(refs):
        f = FIGS_DIR / fname
        if not f.exists():
            missing.append(fname)
        elif f.stat().st_size == 0:
            empty.append(fname)
    assert not missing, f"missing figs: {missing}"
    assert not empty, f"empty figs: {empty}"


def test_required_pitch_figures() -> None:
    """pitch.html에 반드시 참조되어야 하는 핵심 그림 5종."""
    required = [
        "policy_roi_v3_matrix.png",
        "policy_roi_v3_per_line.png",
        "policy_roi_v3_scenarios.png",
        "line_carload_heatmap.png",
        "dispersion_sim.png",
        "od_asymmetry.png",
        "transfer_stations.png",
    ]
    html = PITCH.read_text(encoding="utf-8")
    for f in required:
        assert f"figs/{f}" in html, f"pitch.html missing reference to figs/{f}"
        path = FIGS_DIR / f
        assert path.exists() and path.stat().st_size > 0, f"figs/{f} missing or empty"
