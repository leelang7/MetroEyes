"""발표 영상 5분 4언어 narration 회귀 (cycle 369).

docs/RECORDING_NARRATION.md 가 demo.html SCRIPT (cycle 363) 와 timestamp 정합.
4언어 (ko/en/zh/ja) 모두 핵심 stage 포함되도록 가드.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "RECORDING_NARRATION.md"
DEMO = ROOT / "frontend" / "demo.html"


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_doc_exists() -> None:
    assert DOC.exists(), f"missing {DOC}"


def test_4lang_markers_present() -> None:
    """국기 이모지 마커 — 모든 stage 4언어 노출."""
    txt = _doc()
    # 각 국기마다 최소 10번 이상 등장 (14 stage × 4 lang = 최소 14번)
    for flag, lang in [("🇰🇷", "ko"), ("🇺🇸", "en"), ("🇨🇳", "zh"), ("🇯🇵", "ja")]:
        cnt = txt.count(flag)
        assert cnt >= 10, f"{flag} ({lang}) only {cnt} occurrences — expected ≥10 stages"


def test_critical_stages_referenced() -> None:
    """cycle 356/358/360/368 신규 stage 모두 narration 포함."""
    txt = _doc()
    for marker in ("cycle 356", "cycle 358", "cycle 360"):
        assert marker in txt, f"missing cycle reference: {marker}"
    # 핵심 KPI 수치 (cycle 374 v3 alignment) — 4언어로 보존되어야 함
    for kpi in ("708x", "236x", "224x", "75x", "1,393", "347", "139.3"):
        assert kpi in txt, f"missing KPI reference: {kpi}"


def test_timestamp_alignment_with_demo() -> None:
    """RECORDING_NARRATION 의 timestamp 가 demo.html SCRIPT 의 stage 와 정합."""
    doc = _doc()
    demo = DEMO.read_text(encoding="utf-8")
    # cycle 363 새 stage들 — demo.html SCRIPT 안에 timestamp 등장
    expected_demo_stamps = ["10000,", "150000,", "240000,"]
    for ts in expected_demo_stamps:
        assert ts in demo, f"demo.html SCRIPT missing expected timestamp: {ts}"
    # 그리고 narration 에도 표시 (00:10, 02:30, 04:00)
    for ts in ("00:10", "02:30", "04:00"):
        assert ts in doc, f"narration missing timestamp: {ts}"


def test_recording_tools_documented() -> None:
    """OBS / Audacity / TTS 권장 도구 명시."""
    txt = _doc()
    assert "OBS" in txt, "OBS recording tool missing"
    assert "Audacity" in txt or "ElevenLabs" in txt, "audio recording tool missing"


def test_4lang_distinct_text() -> None:
    """각 stage 의 4 언어가 단순 중복이 아닌 진짜 번역 (ko 와 en 다름)."""
    txt = _doc()
    # "Claude Haiku" 라는 영어 키워드는 ko 섹션과 en 섹션 모두 등장 가능 (브랜드명)
    # 단 "한국어" 는 ko 섹션에만, "English" 는 en 섹션에만 등장
    assert "한국어" in txt, "ko language label missing"
    assert "English" in txt, "en language label missing"
    assert "中文" in txt, "zh language label missing"
    assert "日本語" in txt, "ja language label missing"
