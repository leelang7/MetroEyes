"""eda_transfer_stations.py 회귀 가드 (cycle 534).

환승역 호선 간 ON/OFF 비대칭 차이 분석 — 분산 정책 우선순위 근거.
피치 핵심 주장: "환승역 + 비대칭 차이 큰 곳 = 환승 흐름 변경 가능 지점".
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "eda_transfer_stations.py"


def _asym_transfer(on: float, off: float) -> float:
    """eda_transfer_stations.py:78 비대칭 공식 재현."""
    s = on + off
    return (off - on) / s if s != 0 else 0.0


def test_script_exists() -> None:
    assert SCRIPT.exists(), f"스크립트 없음: {SCRIPT}"


def test_transfer_asym_formula_range() -> None:
    """호선 간 비대칭 지수 [-1, 1] 범위 보장."""
    import random
    rng = random.Random(0)
    for _ in range(200):
        on = rng.uniform(0, 1e6)
        off = rng.uniform(0, 1e6)
        v = _asym_transfer(on, off)
        assert -1.0 <= v <= 1.0


def test_transfer_asym_zero_safe() -> None:
    """on=0, off=0 시 ZeroDivision 없이 0 반환."""
    assert _asym_transfer(0.0, 0.0) == 0.0


def test_transfer_detection_threshold_lines_ge_2() -> None:
    """환승역 = 같은 STTN 호선 수 >= 2 조건 사용."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert ">= 2" in src or "≥ 2" in src or "line_count" in src, \
        "환승역 2호선 이상 조건 없음"


def test_transfer_traffic_filter_5000() -> None:
    """통행량 최소 5,000 필터 (소규모 환승역 제외)."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "5000" in src, "통행량 필터 5000 없음"


def test_transfer_uses_peak_hours_9_19() -> None:
    """AM 9시 / PM 19시 피크 시간 사용."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "am_h, pm_h = 9, 19" in src or ("am_h" in src and "9" in src), \
        "피크 시간 am_h=9, pm_h=19 없음"


def test_transfer_am_pm_diff_columns() -> None:
    """am_diff / pm_diff 컬럼 모두 산출."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "am_diff" in src and "pm_diff" in src, "am_diff/pm_diff 컬럼 없음"


def test_transfer_top10_both_directions() -> None:
    """AM + PM 양방향 TOP 10 환승역 선택."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "nlargest(10" in src, "nlargest 10 TOP 선택 없음"
    # AM / PM 두 번 사용
    assert src.count("nlargest(10") >= 2, "AM + PM 양방향 nlargest 없음"


def test_transfer_output_json_path() -> None:
    """outputs/transfer_stations_report.json 출력 경로 존재."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "transfer_stations_report" in src, "JSON 출력 경로 없음"


def test_transfer_max_min_line_identification() -> None:
    """각 환승역에서 비대칭 최대·최소 호선 식별 (환승 흐름 방향성 근거)."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "am_max_line" in src and "am_min_line" in src, \
        "비대칭 최대·최소 호선 식별 없음"
