"""다중 신호 나우캐스팅 toy — TRIZ #15(동적성) + #1(분할).

문제: 공공 데이터는 30분 평균, 도착정보는 분 단위, CV는 1초 단위.
해결: 칼만 필터로 서로 다른 갱신 주기·노이즈를 가진 3개 신호를 통합 추정.

발표용 시각화: 진짜 점유율 곡선 vs 단일 신호 vs 칼만 fusion.
실행: python scripts/nowcasting_demo.py [--save out.png]
"""
from __future__ import annotations
import argparse
import numpy as np


# 60분(60step) 시뮬. 진짜 점유율은 18시 양봉 출퇴근 곡선 모사.
T = 60
rng = np.random.default_rng(42)


def true_occupancy() -> np.ndarray:
    """18시 출퇴근 양봉. 0~1 정규화."""
    t = np.arange(T)
    # 기본 양봉 + 분 단위 미세 변동
    peaks = 0.55 + 0.30 * np.exp(-((t - 18) ** 2) / 18) \
                 + 0.25 * np.exp(-((t - 42) ** 2) / 24)
    fluctuation = 0.04 * np.sin(t * 0.7) + rng.normal(0, 0.02, T)
    return np.clip(peaks + fluctuation, 0, 1)


def signal_30min(true: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """공공 30분 평균 신호. 매 30분마다만 갱신, 큰 노이즈."""
    idx = np.arange(T)
    avg30 = np.full(T, np.nan)
    obs_idx = []
    for k in (0, 30):
        if k < T:
            window = true[k:min(k + 30, T)]
            value = window.mean() + rng.normal(0, 0.06)
            avg30[k:min(k + 30, T)] = value
            obs_idx.append(k)
    return avg30, np.array(obs_idx)


def signal_arrival(true: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """분 단위 도착정보 — 차편당 점유 추정 (편차 큼)."""
    obs_idx = np.arange(0, T, 4)  # 4분 간격 차편
    obs = true[obs_idx] + rng.normal(0, 0.10, len(obs_idx))
    full = np.full(T, np.nan)
    full[obs_idx] = obs
    return full, obs_idx


def signal_cv(true: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """자체 CV — 1초 단위지만 일부 시각만 카메라 가용 (창문 방향 등)."""
    # 60분 중 25% 시점만 CV 데이터 가용 (실제론 더 많을 수 있음)
    mask = rng.random(T) < 0.25
    obs_idx = np.where(mask)[0]
    obs = true[obs_idx] + rng.normal(0, 0.05, len(obs_idx))  # 노이즈 작음
    full = np.full(T, np.nan)
    full[obs_idx] = obs
    return full, obs_idx


def kalman_fusion(z30: np.ndarray, zarr: np.ndarray, zcv: np.ndarray) -> np.ndarray:
    """1D 칼만 필터 — 3개 관측 채널을 노이즈 R 기준 가중 통합.

    R 작을수록 (CV) 강하게 반영, 클수록 (30분 평균) 약하게.
    """
    R = {"avg30": 0.06**2, "arrival": 0.10**2, "cv": 0.05**2}
    Q = 0.005**2  # 프로세스 노이즈 (점유율 시계열 변화율)

    x = 0.5            # 초기 점유 추정
    P = 0.5            # 초기 분산
    out = np.zeros(T)

    for t in range(T):
        # predict (random walk)
        P = P + Q
        # update — 가용한 모든 관측을 순차 적용
        for z, r in [(z30[t], R["avg30"]),
                     (zarr[t], R["arrival"]),
                     (zcv[t], R["cv"])]:
            if not np.isnan(z):
                K = P / (P + r)
                x = x + K * (z - x)
                P = (1 - K) * P
        out[t] = x
    return out


def report_metrics(true: np.ndarray, fused: np.ndarray,
                   z30: np.ndarray, zarr: np.ndarray) -> None:
    def rmse(a: np.ndarray, b: np.ndarray) -> float:
        m = ~np.isnan(a)
        return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))

    print("\n=== 나우캐스팅 정확도 (RMSE, 낮을수록 좋음) ===")
    print(f"  공공 30분 평균만   RMSE = {rmse(z30, true):.4f}")
    print(f"  도착정보만(보간)   RMSE = {rmse(zarr, true):.4f}")
    print(f"  칼만 fusion        RMSE = {rmse(fused, true):.4f}")

    improvement = (1 - rmse(fused, true) / rmse(z30, true)) * 100
    print(f"\n  ▶ 30분 평균 대비 정확도 +{improvement:.1f}% 개선")


def maybe_plot(true: np.ndarray, z30: np.ndarray, zarr: np.ndarray,
               zcv: np.ndarray, fused: np.ndarray, save: str | None) -> None:
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        # Windows 한글 폰트 — Malgun Gothic 우선, 없으면 영어 fallback.
        for name in ("Malgun Gothic", "NanumGothic", "AppleGothic", "Noto Sans CJK KR"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break
    except ImportError:
        print("\n(matplotlib 미설치 — 그래프 생략. 수치만 출력)")
        return

    t = np.arange(T)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(t, true, "k-", linewidth=2, label="진짜 점유율 (모름)")
    ax.plot(t, z30, "C0--", linewidth=1.5, alpha=0.7, label="공공 30분 평균")
    ax.scatter(t, zarr, c="C1", s=18, alpha=0.6, label="도착정보 (4분)")
    ax.scatter(t, zcv, c="C2", s=18, alpha=0.6, marker="^", label="자체 CV (랜덤)")
    ax.plot(t, fused, "C3-", linewidth=2.5, label="칼만 fusion ★")
    ax.set_xlabel("분 (18시 출퇴근 60분)")
    ax.set_ylabel("점유율")
    ax.set_title("MetroEyes — 다중 신호 나우캐스팅 (TRIZ #15+#1)")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 1)
    plt.tight_layout()
    if save:
        plt.savefig(save, dpi=120)
        print(f"  ▶ 그래프 저장: {save}")
    else:
        plt.show()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--save", default=None, help="PNG 저장 경로")
    args = p.parse_args()

    print("MetroEyes 다중신호 나우캐스팅 데모")
    print("=" * 60)
    print("  공공 30분 평균 + 분 단위 도착정보 + 자체 CV(드문드문)")
    print("  → 칼만 필터로 분 단위 점유 추정")

    true = true_occupancy()
    z30, _ = signal_30min(true)
    zarr, _ = signal_arrival(true)
    zcv, _ = signal_cv(true)
    fused = kalman_fusion(z30, zarr, zcv)

    report_metrics(true, fused, z30, zarr)
    maybe_plot(true, z30, zarr, zcv, fused, args.save)


if __name__ == "__main__":
    main()
