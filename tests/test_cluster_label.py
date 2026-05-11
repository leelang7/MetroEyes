"""cluster_stations.py cluster_label 단위 테스트 (cycle 517).

cluster_label(profile): 48차원 프로파일 → 한글 라벨 (오피스/주거/환승/기타).

profile shape (48,):
  [0:24]  = 승차 (boarding)  at HOURS = [4,5,...,23,0,1,2,3]
  [24:48] = 하차 (alighting)
  AM mask: hours 7-9  → HOURS 인덱스 3,4,5
  PM mask: hours 17-19 → HOURS 인덱스 13,14,15

네트워크/데이터 불필요 — 순수 numpy 로직.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from unittest.mock import MagicMock

np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

# seaborn은 선택적 의존성 — 없으면 mock으로 대체 (cluster_label 자체는 seaborn 불필요)
if "seaborn" not in sys.modules:
    try:
        import seaborn  # noqa: F401
    except ModuleNotFoundError:
        sys.modules["seaborn"] = MagicMock()


def _hours_arr():
    from cluster_stations import HOURS
    return np.array(HOURS)


def _am_idx():
    h = _hours_arr()
    return np.where((h >= 7) & (h <= 9))[0]


def _pm_idx():
    h = _hours_arr()
    return np.where((h >= 17) & (h <= 19))[0]


def _office_profile() -> "np.ndarray":
    """오피스형: 출근 하차↑ (off_am > on_am) + 퇴근 승차↑ (on_pm > off_pm)."""
    p = np.zeros(48)
    am = _am_idx()
    pm = _pm_idx()
    p[am] = 50           # on_am
    p[am + 24] = 300     # off_am (much larger)
    p[pm] = 300          # on_pm (much larger)
    p[pm + 24] = 50      # off_pm
    return p


def _residential_profile() -> "np.ndarray":
    """주거형: 출근 승차↑ (on_am > off_am) + 퇴근 하차↑ (off_pm > on_pm)."""
    p = np.zeros(48)
    am = _am_idx()
    pm = _pm_idx()
    p[am] = 300          # on_am (much larger)
    p[am + 24] = 50      # off_am
    p[pm] = 50           # on_pm
    p[pm + 24] = 300     # off_pm (much larger)
    return p


def _transfer_profile() -> "np.ndarray":
    """환승 허브: AM/PM 모두 on ≈ off (imbalance < 0.35)."""
    p = np.zeros(48)
    am = _am_idx()
    pm = _pm_idx()
    # 거의 동일 → 불균형 ≈ 0
    p[am] = 200
    p[am + 24] = 210     # diff/max = 10/210 ≈ 0.05 < 0.35
    p[pm] = 180
    p[pm + 24] = 185
    return p


def test_cluster_label_office() -> None:
    """오피스형 프로파일 → '오피스형' 라벨 반환."""
    from cluster_stations import cluster_label
    label = cluster_label(_office_profile())
    assert "오피스형" in label, f"오피스형 프로파일 라벨 오류: {label}"


def test_cluster_label_residential() -> None:
    """주거형 프로파일 → '주거형' 라벨 반환."""
    from cluster_stations import cluster_label
    label = cluster_label(_residential_profile())
    assert "주거형" in label, f"주거형 프로파일 라벨 오류: {label}"


def test_cluster_label_transfer_hub() -> None:
    """환승 허브 프로파일 → '환승 허브' 라벨 반환."""
    from cluster_stations import cluster_label
    label = cluster_label(_transfer_profile())
    assert "환승 허브" in label, f"환승 허브 프로파일 라벨 오류: {label}"


def test_cluster_label_flat_profile() -> None:
    """완전 평탄 프로파일 (모두 0) → '기타/평탄형' 또는 '환승 허브'."""
    from cluster_stations import cluster_label
    p = np.zeros(48)
    label = cluster_label(p)
    # 0/0 = 0 imbalance → 환승 허브 조건 충족 (0 < 0.35)
    assert label != "", "빈 라벨 반환"


def test_cluster_label_returns_string() -> None:
    """cluster_label 반환값은 str."""
    from cluster_stations import cluster_label
    label = cluster_label(_office_profile())
    assert isinstance(label, str), f"str 아님: {type(label)}"


def test_hours_constant_length() -> None:
    """HOURS 리스트 길이 = 24 (4시~3시)."""
    from cluster_stations import HOURS
    assert len(HOURS) == 24, f"HOURS 길이 {len(HOURS)} ≠ 24"


def test_hours_constant_starts_at_4() -> None:
    """HOURS[0] = 4 (4시부터 시작)."""
    from cluster_stations import HOURS
    assert HOURS[0] == 4, f"HOURS 시작 {HOURS[0]} ≠ 4"


def test_monte_carlo_ci_structure() -> None:
    """monte_carlo_ci([0.30], n_sims=20) — CI 구조 검증 (빠른 소규모 시뮬)."""
    from policy_roi_v3 import monte_carlo_ci
    result = monte_carlo_ci([0.30], n_sims=20, seed=42)
    # 반환: {"method": ..., "perturbations": ..., "scenarios": {"0.30": {...}}}
    assert "scenarios" in result, "scenarios 키 누락"
    assert "0.30" in result["scenarios"], "'0.30' 시나리오 키 누락"
    ci = result["scenarios"]["0.30"]
    for field in ("net_b_mean", "net_b_p5", "net_b_p95", "roi_x_mean", "n_sims"):
        assert field in ci, f"CI {field} 필드 누락"


def test_monte_carlo_ci_p5_le_p95() -> None:
    """monte_carlo_ci — p5 ≤ mean ≤ p95 (CI 방향성 정상)."""
    from policy_roi_v3 import monte_carlo_ci
    result = monte_carlo_ci([0.30], n_sims=20, seed=42)
    ci = result["scenarios"]["0.30"]
    assert ci["net_b_p5"] <= ci["net_b_mean"], "p5 > mean (CI 역전)"
    assert ci["net_b_mean"] <= ci["net_b_p95"], "mean > p95 (CI 역전)"
