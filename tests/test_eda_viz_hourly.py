"""scripts/eda_viz_hourly.py EDA 시간대별 시각화 단위 테스트 (cycle 530).

순수 pandas 변환 함수 + 상수 — seaborn/matplotlib/loaders 격리 임포트:
- URBAN 상수: 도시철도 필터링 힌트
- is_urban(line): 도시철도 여부 판별
- to_long(df): wide → long format (hour/action/n)

심사 기준 '공공데이터 활용': EDA 파이프라인 신뢰성.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pd = pytest.importorskip("pandas")
np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

# eda_viz_hourly 임포트 시에만 필요한 모듈을 격리 모킹.
# src 패키지 자체는 이미 실제 패키지로 로드됐을 수 있으므로 세밀하게 처리.
_MOCKS = [
    "seaborn",
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.font_manager",
]

_saved: dict = {}
for _m in _MOCKS:
    _saved[_m] = sys.modules.get(_m)
    if _m not in sys.modules:
        sys.modules[_m] = MagicMock()

# src.data_pipeline.loaders: 이미 로드된 경우 유지, 아니면 mock
_LOADER_KEY = "src.data_pipeline.loaders"
_saved[_LOADER_KEY] = sys.modules.get(_LOADER_KEY)
if _LOADER_KEY not in sys.modules:
    # src가 이미 패키지로 존재하면 하위 모듈만 mock
    import importlib
    try:
        import src.data_pipeline.loaders as _real_loaders  # type: ignore
        _real_loaders.fetch_to_parquet = MagicMock(return_value=None)
    except Exception:
        sys.modules[_LOADER_KEY] = MagicMock()

sys.modules.pop("eda_viz_hourly", None)
from eda_viz_hourly import URBAN, is_urban, to_long  # noqa: E402

# 격리 모킹 복원 (matplotlib/seaborn — 다른 테스트 영향 방지)
for _m, _orig in _saved.items():
    if _orig is None:
        sys.modules.pop(_m, None)
    else:
        sys.modules[_m] = _orig


def _make_wide_df() -> "pd.DataFrame":
    """wide-format mock DataFrame (HR_n_GET_ON/OFF_NOPE 컬럼)."""
    rows = []
    for line in ["2호선", "경부선"]:
        for station in ["강남", "선릉"]:
            row = {"SBWY_ROUT_LN_NM": line, "STTN": station}
            for h in range(0, 24):
                row[f"HR_{h}_GET_ON_NOPE"] = float(100 + h * 10)
                row[f"HR_{h}_GET_OFF_NOPE"] = float(80 + h * 8)
            rows.append(row)
    return pd.DataFrame(rows)


def test_urban_constant_not_empty() -> None:
    """URBAN 상수 — 비어있지 않음."""
    assert len(URBAN) > 0, "URBAN 상수 비어 있음"


def test_urban_contains_line_suffix() -> None:
    """URBAN — '호선' 포함 (도시철도 식별)."""
    assert any("호선" in h for h in URBAN), "'호선' 키워드 없음"


def test_is_urban_subway_line() -> None:
    """is_urban('2호선') → True."""
    assert is_urban("2호선") is True, "2호선이 도시철도로 분류 안 됨"


def test_is_urban_korail_line() -> None:
    """is_urban('경부선') → False (코레일)."""
    assert is_urban("경부선") is False, "경부선이 도시철도로 오분류"


def test_is_urban_uisinseol() -> None:
    """is_urban('우이신설선') → True."""
    assert is_urban("우이신설선") is True, "우이신설선 미분류"


def test_to_long_returns_dataframe() -> None:
    """to_long(df) → pd.DataFrame 반환."""
    result = to_long(_make_wide_df())
    assert isinstance(result, pd.DataFrame)


def test_to_long_columns() -> None:
    """to_long(df) → line/station/hour/action/n 컬럼."""
    result = to_long(_make_wide_df())
    for col in ("line", "station", "hour", "action", "n"):
        assert col in result.columns, f"컬럼 {col} 누락"


def test_to_long_action_values() -> None:
    """to_long() — action ∈ {'ride', 'alight'}."""
    result = to_long(_make_wide_df())
    assert set(result["action"].unique()) == {"ride", "alight"}


def test_to_long_hour_range() -> None:
    """to_long() — hour ∈ [0, 23]."""
    result = to_long(_make_wide_df())
    assert result["hour"].between(0, 23).all()
