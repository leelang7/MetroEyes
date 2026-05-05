"""분산 정책 시뮬 EDA — 실 데이터 위 30% 응답률 적용 시 시간대 평탄화 효과.

배경: 정책 ROI v3는 "응답률 30% → 1,393억/년" 을 주장.
이 스크립트는 그 가정의 *물리적 효과*를 실 데이터로 보여줌:
  - data/processed/subway_time_202602.parquet 의 HR_h_GET_ON_NOPE 시간대 합계
  - 피크 시간(7~9 / 17~19)의 X% 인원이 ±1~2시간 분산된다면 곡선이 어떻게 평탄화?
  - σ (표준편차) / max-min / 피크 감소율 정량 비교

산출:
  outputs/dispersion_sim.png         — before/after 시간대 곡선 비교
  outputs/dispersion_sim_report.json — 평탄화 정량 지표
  outputs/dispersion_sim_lines.png   — 호선별 9개 패널 (1~9호선)

발표 활용: pitch.html figure 추가 — "30% 응답률은 σ를 N% 줄임" → 정책 효과의 직관적 근거.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed" / "subway_time_202602.parquet"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

PEAK_AM = (7, 8, 9)
PEAK_PM = (17, 18, 19)
RESPONSE_RATE = 0.30   # ROI v3 기준
DISPERSE_FRAC = 0.45   # 응답한 사람 중 분산 가능 비율 (나머지는 시간 강제 이동)


def disperse(curve: np.ndarray, response: float = RESPONSE_RATE,
             d_frac: float = DISPERSE_FRAC) -> np.ndarray:
    """피크 시각의 (response × d_frac) 인원을 ±1~2시간 균등 분산.

    예: 8시 100명 × 0.30 × 0.45 = 13.5명이 6/7/9/10시로 분산.
    """
    out = curve.astype(float).copy()
    for h in (*PEAK_AM, *PEAK_PM):
        if h >= len(curve): continue
        moved = curve[h] * response * d_frac
        out[h] -= moved
        # ±1, ±2 시간 25% / 25% / 25% / 25% 균등 (피크 외부에)
        for dh, w in [(-2, 0.25), (-1, 0.25), (1, 0.25), (2, 0.25)]:
            tgt = h + dh
            if 0 <= tgt < len(curve) and tgt not in (*PEAK_AM, *PEAK_PM):
                out[tgt] += moved * w
    return out


def metrics(curve: np.ndarray) -> dict:
    return {
        "max": float(curve.max()),
        "min": float(curve[curve > 0].min()) if (curve > 0).any() else 0,
        "std": float(curve.std()),
        "peak_avg": float(np.mean([curve[h] for h in (*PEAK_AM, *PEAK_PM) if h < len(curve)])),
        "offpeak_avg": float(np.mean([curve[h] for h in range(5, 24)
                                      if h < len(curve) and h not in (*PEAK_AM, *PEAK_PM)])),
    }


def main():
    print("=" * 72)
    print("MetroEyes EDA — 분산 시뮬: 실 데이터 위 30% 응답률 평탄화 효과")
    print("=" * 72)

    if not DATA.exists():
        raise SystemExit(f"데이터 없음: {DATA}")
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise SystemExit(f"필수 패키지 없음: {e}")

    df = pd.read_parquet(DATA)
    print(f"[load] {len(df):,}행 / {df['SBWY_ROUT_LN_NM'].nunique()}호선")

    main_lines = [f"{i}호선" for i in range(1, 10)]
    df = df[df["SBWY_ROUT_LN_NM"].isin(main_lines)].copy()

    hours = list(range(5, 24))
    # 전체 호선 합계 곡선
    total_before = np.zeros(24)
    line_curves: dict[str, np.ndarray] = {}
    for line in main_lines:
        sub = df[df["SBWY_ROUT_LN_NM"] == line]
        if sub.empty: continue
        line_c = np.zeros(24)
        for h in hours:
            col = f"HR_{h}_GET_ON_NOPE"
            if col in sub.columns:
                # 28일 평균 → 일평균
                line_c[h] = sub[col].sum() / 28.0
        line_curves[line] = line_c
        total_before += line_c
    print(f"[curve] 일평균 ON 시간대별 곡선 (5~23h)")

    total_after = disperse(total_before)
    m_before = metrics(total_before)
    m_after = metrics(total_after)

    # 정량 결과
    sigma_drop = (m_before["std"] - m_after["std"]) / m_before["std"] * 100
    peak_drop = (m_before["peak_avg"] - m_after["peak_avg"]) / m_before["peak_avg"] * 100
    offpeak_lift = (m_after["offpeak_avg"] - m_before["offpeak_avg"]) / m_before["offpeak_avg"] * 100
    peak_offpeak_ratio_before = m_before["peak_avg"] / m_before["offpeak_avg"]
    peak_offpeak_ratio_after = m_after["peak_avg"] / m_after["offpeak_avg"]

    print(f"\n[result] σ {m_before['std']:.0f} → {m_after['std']:.0f}  ({-sigma_drop:+.1f}%)")
    print(f"[result] 피크 평균 {m_before['peak_avg']:.0f} → {m_after['peak_avg']:.0f}  ({-peak_drop:+.1f}%)")
    print(f"[result] 비피크 평균 {m_before['offpeak_avg']:.0f} → {m_after['offpeak_avg']:.0f}  ({offpeak_lift:+.1f}%)")
    print(f"[result] 피크/비피크 비율 {peak_offpeak_ratio_before:.2f} → {peak_offpeak_ratio_after:.2f}")

    # 1. 전체 곡선 plot
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.plot(range(24), total_before / 1e6, "-", color="#ff5e57", linewidth=2.5,
            label=f"현재 (피크/비피크 {peak_offpeak_ratio_before:.1f}x)")
    ax.plot(range(24), total_after / 1e6, "-", color="#7dd3d3", linewidth=2.5,
            label=f"분산 후 30% 응답 (피크/비피크 {peak_offpeak_ratio_after:.1f}x)")
    ax.fill_between(range(24), total_before / 1e6, total_after / 1e6,
                    where=(total_after < total_before),
                    color="#ff5e57", alpha=0.15, label="피크 감소")
    ax.fill_between(range(24), total_before / 1e6, total_after / 1e6,
                    where=(total_after > total_before),
                    color="#10b981", alpha=0.15, label="비피크 증가")
    for h in (*PEAK_AM, *PEAK_PM):
        ax.axvline(h, color="white", alpha=0.05, linewidth=0.5)
    ax.set_xlabel("시각 (hour)", color="white")
    ax.set_ylabel("일평균 승차 인원 (백만 명)", color="white")
    ax.set_title(f"분산 정책 효과 — σ {-sigma_drop:.1f}% / 피크 {-peak_drop:.1f}% / "
                 f"비피크 {offpeak_lift:+.1f}% (응답률 30%, 1~9호선 합계)",
                 color="white", fontsize=11)
    ax.legend(loc="upper left", framealpha=0.85, fontsize=10)
    ax.set_xticks(range(5, 24))
    ax.grid(alpha=0.1)
    fig.tight_layout()
    fig.savefig(OUT / "dispersion_sim.png", dpi=130, bbox_inches="tight",
                facecolor="#04060a")
    plt.close(fig)
    print(f"[save] {OUT / 'dispersion_sim.png'}")

    # 2. 호선별 9개 패널
    fig2, axs = plt.subplots(3, 3, figsize=(13, 10), sharex=True)
    axs = axs.flatten()
    for i, line in enumerate(main_lines):
        if line not in line_curves: continue
        c_b = line_curves[line]
        c_a = disperse(c_b)
        axs[i].plot(range(24), c_b / 1e3, color="#ff5e57", linewidth=1.8, label="현재")
        axs[i].plot(range(24), c_a / 1e3, color="#7dd3d3", linewidth=1.8, label="분산 후")
        axs[i].set_title(line, color="white", fontsize=10)
        axs[i].grid(alpha=0.1)
        axs[i].set_xticks(range(5, 24, 4))
        if i == 0: axs[i].legend(fontsize=8, loc="upper right")
    fig2.suptitle("호선별 분산 효과 (응답률 30%) — 천 명/시", color="white", fontsize=12)
    fig2.tight_layout()
    fig2.savefig(OUT / "dispersion_sim_lines.png", dpi=120, bbox_inches="tight",
                 facecolor="#04060a")
    plt.close(fig2)
    print(f"[save] {OUT / 'dispersion_sim_lines.png'}")

    # 3. JSON 리포트
    report = {
        "response_rate": RESPONSE_RATE,
        "disperse_fraction": DISPERSE_FRAC,
        "peak_hours": [*PEAK_AM, *PEAK_PM],
        "metrics_before": m_before,
        "metrics_after": m_after,
        "sigma_reduction_pct": -sigma_drop,
        "peak_reduction_pct": -peak_drop,
        "offpeak_lift_pct": offpeak_lift,
        "peak_offpeak_ratio_before": peak_offpeak_ratio_before,
        "peak_offpeak_ratio_after": peak_offpeak_ratio_after,
        "data_source": str(DATA.relative_to(ROOT)),
        "n_lines": len(line_curves),
    }
    (OUT / "dispersion_sim_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[save] {OUT / 'dispersion_sim_report.json'}")
    print("\n[done] 정책 분산 EDA 완료 — pitch.html figure 갱신 가능")


if __name__ == "__main__":
    main()
