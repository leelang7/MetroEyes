"""차등 보상 정책 _bonus_krw 회귀 — pitch FAQ Q6 광고 산정 근거 가드.

- ₩200 (기본) / +₩100 (OD 우선) / +₩200 (환승역) 가중치 정확성
- AM/PM 시간대 외 → 0원 (기본만)
- _priority_cache 로딩 후 의도된 tier 매칭

Note: time.localtime() 의존성 — patch로 시간대 고정.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch
import time as _time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _make_struct_time(hour: int) -> _time.struct_time:
    return _time.struct_time((2026, 5, 7, hour, 0, 0, 2, 127, 0))


def _load_module():
    """우회 import — websockets 없을 때도 일단 _bonus_krw만 isolated load 시도."""
    import importlib
    return importlib.import_module("src.cv.lite_server")


def test_basic_returns_zero_outside_peak() -> None:
    """비피크 시간(13시) → 모두 basic 0원."""
    mod = _load_module()
    with patch.object(mod.time, "localtime", return_value=_make_struct_time(13)):
        amount, tier = mod._bonus_krw("삼성(무역센터)")
        assert amount == 0
        assert tier == "basic"


def test_am_peak_od_arrival_station() -> None:
    """오전 9시 + OD 도착 우선 역 (삼성) → +₩100, tier=od."""
    mod = _load_module()
    mod._priority_cache.clear()
    mod._priority_cache["od_arrival"] = {"삼성(무역센터)"}
    mod._priority_cache["od_departure"] = set()
    mod._priority_cache["transfer"] = set()
    mod._priority_cache["loaded"] = True
    with patch.object(mod.time, "localtime", return_value=_make_struct_time(9)):
        amount, tier = mod._bonus_krw("삼성(무역센터)")
    assert amount == 100, f"OD arrival expected +100, got {amount}"
    assert tier == "od"


def test_pm_peak_od_departure_station() -> None:
    """오후 19시 + OD 출발 우선 역 (시청) → +₩100, tier=od."""
    mod = _load_module()
    mod._priority_cache.clear()
    mod._priority_cache["od_arrival"] = set()
    mod._priority_cache["od_departure"] = {"시청"}
    mod._priority_cache["transfer"] = set()
    mod._priority_cache["loaded"] = True
    with patch.object(mod.time, "localtime", return_value=_make_struct_time(19)):
        amount, tier = mod._bonus_krw("시청")
    assert amount == 100
    assert tier == "od"


def test_transfer_priority_outranks_od() -> None:
    """환승역이 OD보다 우선 — 충무로 환승 → +₩200, tier=transfer."""
    mod = _load_module()
    mod._priority_cache.clear()
    mod._priority_cache["od_arrival"] = {"충무로"}   # 환승 set이 우선해야 함
    mod._priority_cache["od_departure"] = set()
    mod._priority_cache["transfer"] = {"충무로"}
    mod._priority_cache["loaded"] = True
    with patch.object(mod.time, "localtime", return_value=_make_struct_time(9)):
        amount, tier = mod._bonus_krw("충무로")
    assert amount == 200
    assert tier == "transfer"


def test_unknown_station_basic() -> None:
    """매칭되지 않는 역 → basic 0."""
    mod = _load_module()
    mod._priority_cache.clear()
    mod._priority_cache["od_arrival"] = set()
    mod._priority_cache["od_departure"] = set()
    mod._priority_cache["transfer"] = set()
    mod._priority_cache["loaded"] = True
    with patch.object(mod.time, "localtime", return_value=_make_struct_time(8)):
        amount, tier = mod._bonus_krw("랜덤역_매칭없음")
    assert amount == 0
    assert tier == "basic"


def test_empty_station_basic() -> None:
    """빈 문자열 → basic 0."""
    mod = _load_module()
    amount, tier = mod._bonus_krw("")
    assert amount == 0
    assert tier == "basic"
