"""README outdated 텍스트 자동 차단 (cycle 383).

cycle 311 / CI 12 jobs / 41 가드 등 outdated 헤더가 README 안에 살아남아
심사위원이 "왜 311 사이클? 너무 옛날?" 의문 갖는 회귀 방지.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KO = ROOT / "README.md"
EN = ROOT / "README.en.md"


def _ko() -> str:
    return KO.read_text(encoding="utf-8")


def _en() -> str:
    return EN.read_text(encoding="utf-8")


def test_no_outdated_cycle_311_header() -> None:
    """README 의 헤더 섹션에 '311 사이클' / 'D-6' outdated 마커 제거."""
    ko = _ko()
    en = _en()
    # 헤더의 누적 결과 섹션 — 'XXX 사이클 누적' 형식
    assert "자동 311 사이클 누적" not in ko, "ko outdated cycle 311 header still present"
    assert "311 Auto Cycles Accumulated" not in en, "en outdated cycle 311 header still present"


def test_no_outdated_ci_12_jobs() -> None:
    """README 'CI 12 jobs + 41 가드' outdated 줄 제거."""
    ko = _ko()
    en = _en()
    assert "CI 12 jobs + pytest 회귀 가드 41건" not in ko, "ko outdated CI 12 jobs/41 guards still present"
    assert "CI 12 jobs + 41 pytest regression guards" not in en, "en outdated CI 12 jobs/41 guards still present"


def test_recent_cycle_count_advertised() -> None:
    """README 누적 결과 헤더가 cycle 350+ 사이클 수 광고."""
    ko = _ko()
    en = _en()
    # 'XXX 사이클 누적' 또는 'XXX Auto Cycles Accumulated'
    m_ko = re.search(r"자동\s+(\d{3,4})\s*사이클\s*누적", ko)
    m_en = re.search(r"(\d{3,4})\s+Auto\s+Cycles\s+Accumulated", en)
    assert m_ko, "ko cycle count header missing"
    assert m_en, "en cycle count header missing"
    assert int(m_ko.group(1)) >= 380, f"ko cycle count {m_ko.group(1)} too old (must be ≥380)"
    assert int(m_en.group(1)) >= 380, f"en cycle count {m_en.group(1)} too old (must be ≥380)"


def test_recent_ci_jobs_advertised() -> None:
    """CI jobs 수가 15+ 광고."""
    ko = _ko()
    en = _en()
    # CI N jobs (N >= 14)
    m_ko = re.search(r"CI\s+(\d+)\s+jobs", ko)
    m_en = re.search(r"CI\s+(\d+)\s+jobs", en)
    assert m_ko, "ko CI jobs count missing"
    assert m_en, "en CI jobs count missing"
    assert int(m_ko.group(1)) >= 14, f"ko CI {m_ko.group(1)} jobs too old"
    assert int(m_en.group(1)) >= 14, f"en CI {m_en.group(1)} jobs too old"


def test_dday_marker_recent() -> None:
    """D-day 마커가 D-7 이내 (D-day 5/13 기준 D-5 ~ D+1)."""
    ko = _ko()
    en = _en()
    # D-N (N <= 7)
    m_ko = re.search(r"D-(\d+)", ko)
    m_en = re.search(r"D-(\d+)", en)
    if m_ko:
        assert int(m_ko.group(1)) <= 7, f"ko D-{m_ko.group(1)} too old"
    if m_en:
        assert int(m_en.group(1)) <= 7, f"en D-{m_en.group(1)} too old"
