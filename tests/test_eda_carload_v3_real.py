"""eda_carload_v3_real.py 회귀 가드 (cycle 535).

실 CardSubwayTime parquet 직접 GBR 회귀 — 칸별 점유 예측 핵심 모델.
피치 근거: "칸 컬럼 부재를 자체 CV+공공데이터로 보완하는 예측 모델".
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "eda_carload_v3_real.py"


def test_script_exists() -> None:
    assert SCRIPT.exists(), f"스크립트 없음: {SCRIPT}"


def test_line_cars_all_9_lines() -> None:
    """LINE_CARS — 1~9호선 9개 모두 정의."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from eda_carload_v3_real import LINE_CARS
    for i in range(1, 10):
        key = f"{i}호선"
        assert key in LINE_CARS, f"{key} LINE_CARS 미정의"


def test_line_cars_values_positive() -> None:
    """LINE_CARS — 모든 칸 수 양수."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from eda_carload_v3_real import LINE_CARS
    for line, cars in LINE_CARS.items():
        assert cars > 0, f"{line} 칸 수 {cars} ≤ 0"


def test_line_2_has_10_cars() -> None:
    """2호선 = 10량 (서울 지하철 표준)."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from eda_carload_v3_real import LINE_CARS
    assert LINE_CARS["2호선"] == 10


def test_line_9_has_6_cars() -> None:
    """9호선 = 6량."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from eda_carload_v3_real import LINE_CARS
    assert LINE_CARS["9호선"] == 6


def test_peak_hours_feature_in_script() -> None:
    """is_peak_am (7,8,9) / is_peak_pm (17,18,19) 피크 특징 포함."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "is_peak_am" in src and "is_peak_pm" in src, "피크 특징 없음"
    assert "7, 8, 9" in src or "[7, 8, 9]" in src, "AM 피크 시간 없음"
    assert "17, 18, 19" in src or "[17, 18, 19]" in src, "PM 피크 시간 없음"


def test_5fold_cross_validation() -> None:
    """5-fold CV 검증 (KFold(n_splits=5))."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "KFold" in src or "cross_val" in src, "CV 없음"
    assert "n_splits=5" in src or "cv=5" in src or "cv=kf" in src, "5-fold 설정 없음"


def test_output_json_r2_key() -> None:
    """결과 JSON에 cv_r2_mean 키 존재."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert '"cv_r2_mean"' in src, "JSON 출력에 cv_r2_mean 없음"


def test_gbr_model_used() -> None:
    """GradientBoostingRegressor 사용."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "GradientBoosting" in src, "GBR 모델 없음"


def test_cardsubwaytime_column_format() -> None:
    """CardSubwayTime API HR_{h}_GET_ON_NOPE 컬럼 사용."""
    src = SCRIPT.read_text(encoding="utf-8")
    assert "GET_ON_NOPE" in src, "CardSubwayTime ON 컬럼 없음"
