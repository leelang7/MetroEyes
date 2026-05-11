"""scripts/nowcasting_demo.py 칼만 필터 융합 단위 테스트 (cycle 525).

TRIZ #15(동적성) 다중신호 나우캐스팅 — 심사 '실현가능성' 핵심 수치:
- true_occupancy(): 60step 양봉 시뮬 점유율 곡선
- signal_30min/arrival/cv(): 3개 관측 채널 노이즈 신호
- kalman_fusion(): 칼만 가중 통합 → RMSE 개선 입증

네트워크/데이터 불필요 — 순수 numpy.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def test_true_occupancy_shape() -> None:
    """true_occupancy() → shape (60,)."""
    from nowcasting_demo import true_occupancy, T
    occ = true_occupancy()
    assert occ.shape == (T,), f"shape {occ.shape} ≠ ({T},)"


def test_true_occupancy_bounded() -> None:
    """true_occupancy() → [0, 1] 범위."""
    from nowcasting_demo import true_occupancy
    occ = true_occupancy()
    assert occ.min() >= 0.0, f"min {occ.min()} < 0"
    assert occ.max() <= 1.0, f"max {occ.max()} > 1"


def test_true_occupancy_bimodal() -> None:
    """true_occupancy() — 피크가 t=15~25 또는 t=35~50 근처에 존재 (양봉)."""
    from nowcasting_demo import true_occupancy
    occ = true_occupancy()
    am_peak = occ[10:30].max()
    pm_peak = occ[35:55].max()
    valley = occ[25:38].min()
    assert am_peak > valley, "AM 피크가 계곡보다 높아야"
    assert pm_peak > valley, "PM 피크가 계곡보다 높아야"


def test_signal_30min_shape() -> None:
    """signal_30min(true) → avg30 shape (60,)."""
    from nowcasting_demo import true_occupancy, signal_30min, T
    occ = true_occupancy()
    avg30, obs_idx = signal_30min(occ)
    assert avg30.shape == (T,), f"avg30 shape {avg30.shape} ≠ ({T},)"


def test_signal_30min_obs_indices() -> None:
    """signal_30min() — 관측 시점 = [0, 30] (30분 간격)."""
    from nowcasting_demo import true_occupancy, signal_30min
    occ = true_occupancy()
    _, obs_idx = signal_30min(occ)
    assert 0 in obs_idx, "t=0 관측 누락"
    assert 30 in obs_idx, "t=30 관측 누락"


def test_signal_arrival_obs_every_4min() -> None:
    """signal_arrival() — 4분 간격 관측 (15개)."""
    from nowcasting_demo import true_occupancy, signal_arrival, T
    occ = true_occupancy()
    _, obs_idx = signal_arrival(occ)
    expected = len(range(0, T, 4))
    assert len(obs_idx) == expected, f"관측 수 {len(obs_idx)} ≠ {expected}"


def test_signal_cv_coverage() -> None:
    """signal_cv() — 약 25% 시점 가용 (±50% 허용)."""
    from nowcasting_demo import true_occupancy, signal_cv, T
    occ = true_occupancy()
    _, obs_idx = signal_cv(occ)
    ratio = len(obs_idx) / T
    assert 0.10 <= ratio <= 0.50, f"CV 커버리지 {ratio:.0%} 범위 벗어남"


def test_kalman_fusion_shape() -> None:
    """kalman_fusion() → shape (60,)."""
    from nowcasting_demo import true_occupancy, signal_30min, signal_arrival, signal_cv
    from nowcasting_demo import kalman_fusion, T
    occ = true_occupancy()
    z30, _ = signal_30min(occ)
    zarr, _ = signal_arrival(occ)
    zcv, _ = signal_cv(occ)
    fused = kalman_fusion(z30, zarr, zcv)
    assert fused.shape == (T,), f"shape {fused.shape} ≠ ({T},)"


def test_kalman_fusion_rmse_improvement() -> None:
    """칼만 fusion RMSE < 30분 평균 RMSE (다중신호 융합 효과)."""
    from nowcasting_demo import true_occupancy, signal_30min, signal_arrival, signal_cv
    from nowcasting_demo import kalman_fusion
    occ = true_occupancy()
    z30, _ = signal_30min(occ)
    zarr, _ = signal_arrival(occ)
    zcv, _ = signal_cv(occ)
    fused = kalman_fusion(z30, zarr, zcv)

    def rmse(pred: np.ndarray, true: np.ndarray) -> float:
        m = ~np.isnan(pred)
        return float(np.sqrt(np.mean((pred[m] - true[m]) ** 2)))

    rmse_30 = rmse(z30, occ)
    rmse_fused = rmse(fused, occ)
    assert rmse_fused < rmse_30, \
        f"칼만 RMSE {rmse_fused:.4f} ≥ 30분평균 RMSE {rmse_30:.4f}"


def test_kalman_fusion_nonneg() -> None:
    """칼만 fusion 결과 — 음수 추정치 없음."""
    from nowcasting_demo import true_occupancy, signal_30min, signal_arrival, signal_cv
    from nowcasting_demo import kalman_fusion
    occ = true_occupancy()
    z30, _ = signal_30min(occ)
    zarr, _ = signal_arrival(occ)
    zcv, _ = signal_cv(occ)
    fused = kalman_fusion(z30, zarr, zcv)
    assert (fused >= 0).all(), "음수 추정치 존재"
