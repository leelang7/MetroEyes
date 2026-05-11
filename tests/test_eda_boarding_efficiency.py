"""tests/test_eda_boarding_efficiency.py — cycle 539 회귀 가드 (14 tests)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.eda_boarding_efficiency import (
    BOARDING_SEC_PER_PERSON,
    DOOR_WIDTH_M,
    MONTH,
    PEAK_HOURS,
    boarding_efficiency_by_station,
    congestion_index,
    estimate_dwell_time,
    load_cardsubwaytime,
)


# --- 상수 가드 ---
def test_month_format():
    assert len(MONTH) == 6 and MONTH.isdigit()


def test_boarding_sec_positive():
    assert BOARDING_SEC_PER_PERSON > 0


def test_door_width_positive():
    assert DOOR_WIDTH_M > 0


def test_peak_hours_am_pm():
    am = [h for h in PEAK_HOURS if h < 12]
    pm = [h for h in PEAK_HOURS if h >= 12]
    assert len(am) >= 2 and len(pm) >= 2


def test_peak_hours_no_duplicate():
    assert len(PEAK_HOURS) == len(set(PEAK_HOURS))


# --- estimate_dwell_time ---
def test_dwell_zero_boarding():
    assert estimate_dwell_time(0) == 0.0


def test_dwell_positive_boarding():
    d = estimate_dwell_time(1000)
    assert d > 0


def test_dwell_more_boarding_longer():
    assert estimate_dwell_time(2000) > estimate_dwell_time(1000)


def test_dwell_more_cars_shorter():
    assert estimate_dwell_time(1000, cars=20) < estimate_dwell_time(1000, cars=5)


# --- load / boarding_efficiency_by_station ---
def test_load_returns_dataframe():
    df = load_cardsubwaytime(MONTH)
    assert len(df) > 0


def test_boarding_efficiency_columns():
    df = load_cardsubwaytime(MONTH)
    eff = boarding_efficiency_by_station(df)
    for col in ("SUB_STA_NM", "peak_boarding", "est_dwell_sec", "peak_ratio"):
        assert col in eff.columns, f"Missing column: {col}"


def test_boarding_efficiency_sorted_desc():
    df = load_cardsubwaytime(MONTH)
    eff = boarding_efficiency_by_station(df)
    vals = list(eff["est_dwell_sec"])
    assert vals == sorted(vals, reverse=True)


def test_dwell_sec_all_positive():
    df = load_cardsubwaytime(MONTH)
    eff = boarding_efficiency_by_station(df)
    assert (eff["est_dwell_sec"] >= 0).all()


# --- congestion_index ---
def test_congestion_index_positive():
    df = load_cardsubwaytime(MONTH)
    eff = boarding_efficiency_by_station(df)
    row = eff.iloc[0]
    ci = congestion_index(row)
    assert ci >= 0
