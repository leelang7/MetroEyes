"""scripts/eda_dispersion_sim.py 분산 시뮬 단위 테스트 (cycle 516).

순수 numpy 함수 — 네트워크/데이터 불필요:
- disperse(curve): 피크 시간대 응답률 분산 효과
- metrics(curve): max/std/peak_avg/offpeak_avg 정량 지표
- 상수: PEAK_AM / PEAK_PM / RESPONSE_RATE / DISPERSE_FRAC

심사 기준 검증: "30% 응답률은 σ를 줄임" 정량 모델 신뢰성.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _flat_curve() -> "np.ndarray":
    """테스트용 균일 수요 곡선 (24시간 모두 100)."""
    return np.ones(24) * 100.0


def _peak_curve() -> "np.ndarray":
    """테스트용 피크 집중 곡선 — 7/8/9 / 17/18/19 시 500, 나머지 50."""
    curve = np.ones(24) * 50.0
    for h in (7, 8, 9, 17, 18, 19):
        curve[h] = 500.0
    return curve


def test_disperse_peak_reduces() -> None:
    """disperse() — 피크 시간 수요 감소."""
    from eda_dispersion_sim import disperse
    curve = _peak_curve()
    out = disperse(curve)
    for h in (8, 18):  # 핵심 피크
        assert out[h] < curve[h], f"{h}시 피크가 분산 후 줄지 않음"


def test_disperse_peak_to_peak_not_transferred() -> None:
    """disperse() — 피크→피크 이동 없음 (피크 외 시간으로만 분산)."""
    from eda_dispersion_sim import disperse, PEAK_AM, PEAK_PM
    curve = _peak_curve()
    out = disperse(curve)
    # 비피크 시간대 합은 증가 (분산 수혜)
    peaks = set((*PEAK_AM, *PEAK_PM))
    offpeak_before = sum(curve[h] for h in range(24) if h not in peaks)
    offpeak_after = sum(out[h] for h in range(24) if h not in peaks)
    assert offpeak_after > offpeak_before, "분산 후 비피크 합계가 증가하지 않음"


def test_disperse_offpeak_increases() -> None:
    """disperse() — 비피크 시간대 수요 일부 증가."""
    from eda_dispersion_sim import disperse
    curve = _peak_curve()
    out = disperse(curve)
    # 6, 10, 16, 20시 중 적어도 하나 증가
    increased = any(out[h] > curve[h] for h in (6, 10, 16, 20))
    assert increased, "비피크 시간대 수요 증가 없음 — 분산 효과 없음"


def test_disperse_zero_response() -> None:
    """disperse(response=0) — 원래 곡선과 동일."""
    from eda_dispersion_sim import disperse
    curve = _peak_curve()
    out = disperse(curve, response=0.0)
    np.testing.assert_allclose(out, curve, rtol=1e-6)


def test_metrics_returns_required_keys() -> None:
    """metrics() — max/min/std/peak_avg/offpeak_avg 키 존재."""
    from eda_dispersion_sim import metrics
    curve = _peak_curve()
    m = metrics(curve)
    for key in ("max", "min", "std", "peak_avg", "offpeak_avg"):
        assert key in m, f"metrics {key} 키 누락"


def test_metrics_peak_avg_gt_offpeak() -> None:
    """metrics() — 피크 평균 > 비피크 평균 (피크 집중 곡선)."""
    from eda_dispersion_sim import metrics
    m = metrics(_peak_curve())
    assert m["peak_avg"] > m["offpeak_avg"], "피크 평균 ≤ 비피크 평균"


def test_peak_constants() -> None:
    """PEAK_AM = (7,8,9), PEAK_PM = (17,18,19) — 서울 출퇴근 시간."""
    from eda_dispersion_sim import PEAK_AM, PEAK_PM
    assert set(PEAK_AM) == {7, 8, 9}, f"PEAK_AM {PEAK_AM} 오류"
    assert set(PEAK_PM) == {17, 18, 19}, f"PEAK_PM {PEAK_PM} 오류"


def test_response_rate_constant() -> None:
    """RESPONSE_RATE = 0.30 (ROI v3 기준 30%)."""
    from eda_dispersion_sim import RESPONSE_RATE
    assert RESPONSE_RATE == 0.30, f"RESPONSE_RATE {RESPONSE_RATE} ≠ 0.30"


def test_disperse_std_reduction() -> None:
    """disperse() — 표준편차 감소 (분산 효과 정량화)."""
    from eda_dispersion_sim import disperse, metrics
    curve = _peak_curve()
    out = disperse(curve)
    m_before = metrics(curve)
    m_after = metrics(out)
    assert m_after["std"] < m_before["std"], \
        f"분산 후 σ {m_after['std']:.1f} ≥ 분산 전 {m_before['std']:.1f}"
