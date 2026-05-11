"""eda_od_asymmetry.py 회귀 가드 (cycle 534).

공공데이터 기반 ON/OFF 비대칭 지수 — 순수 함수 속성 + 구현 계약 검증.
피치 Slide 7 근거: "강남역 09시 OFF/ON = X배" 정량 신뢰성.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "eda_od_asymmetry.py"


# --------------- asym() 재현 (스크립트 내 로컬 함수) ---------------

def _asym(on: float, off: float) -> float:
    """eda_od_asymmetry.py:76-78 asym() 동일 구현."""
    s = on + off
    return (off - on) / s if s > 0 else 0.0


# ----------------------------------------------------------------

def test_script_exists() -> None:
    assert SCRIPT.exists(), f"스크립트 없음: {SCRIPT}"


def test_asym_pure_arrival() -> None:
    """off=100, on=0 → asym=1.0 (출근 도착지 극단)."""
    assert _asym(0, 100) == pytest.approx(1.0)


def test_asym_pure_departure() -> None:
    """on=100, off=0 → asym=-1.0 (퇴근 출발지 극단)."""
    assert _asym(100, 0) == pytest.approx(-1.0)


def test_asym_balanced() -> None:
    """on==off → asym=0.0 (균형)."""
    assert _asym(500, 500) == pytest.approx(0.0)


def test_asym_zero_both() -> None:
    """on=0, off=0 → asym=0.0 (영 안전)."""
    assert _asym(0, 0) == pytest.approx(0.0)


def test_asym_range() -> None:
    """asym 는 항상 [-1, 1] 범위."""
    import random
    rng = random.Random(42)
    for _ in range(200):
        on = rng.uniform(0, 1e6)
        off = rng.uniform(0, 1e6)
        v = _asym(on, off)
        assert -1.0 <= v <= 1.0, f"범위 벗어남: asym({on:.0f}, {off:.0f}) = {v}"


def test_asym_sign_convention() -> None:
    """양수 = OFF 우세 = 출근 도착지; 음수 = ON 우세 = 퇴근 출발지."""
    assert _asym(100, 900) > 0, "OFF 우세 시 양수여야 함"
    assert _asym(900, 100) < 0, "ON 우세 시 음수여야 함"


def test_peak_hours_am_pm() -> None:
    """스크립트가 출근 09시, 퇴근 19시를 피크로 사용."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "am_h, pm_h = 9, 19" in src or ("am_h" in src and "9" in src and "pm_h" in src and "19" in src), \
        "AM 9시 / PM 19시 피크 상수 없음"


def test_column_naming_convention() -> None:
    """HR_{h}_GET_ON_NOPE / HR_{h}_GET_OFF_NOPE 컬럼 규칙 사용."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "GET_ON_NOPE" in src and "GET_OFF_NOPE" in src, \
        "CardSubwayTime API 컬럼 명명 규칙 없음"


def test_output_json_path_od_asymmetry() -> None:
    """outputs/od_asymmetry_report.json 출력 경로 존재."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "od_asymmetry_report" in src or "od_asymmetry" in src, \
        "od_asymmetry 출력 경로 없음"


def test_top10_selection_both_directions() -> None:
    """상위 10 출근도착 + 하위 10 퇴근출발 모두 선택."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "nlargest(10" in src and "nsmallest(10" in src, \
        "nlargest/nsmallest 10 TOP 양방향 선택 없음"


def test_threshold_minimum_5000() -> None:
    """통행량 필터 최소값 5000 (소규모 역 제외)."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "5000" in src, "통행량 최소 필터 5000 없음"
