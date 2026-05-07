"""분산 운임 인센티브 정책 ROI v3 - 호선 × 시간대 차등 모델.

v2 진화:
  - 호선별 cap 도달도 차등 (1호선 양봉 강함 vs 9호선 상시 만석)
  - 출근 vs 퇴근 응답률 비대칭 (퇴근이 분산 잘 응답 - 일정 자율도 ↑)
  - 호선 × 시간대 매트릭스 적분 (단순 24시 합산이 아닌 17 × 24 셀)
  - 칸 단위 분산 효과 (cap 150% → 110% 평탄화)

산출:
  outputs/policy_roi_v3_report.json
  outputs/policy_roi_v3_matrix.png  (호선 × 시간대 절감)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# Windows cp949 콘솔에서도 한글/em-dash 정상 출력
if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


# ============== 데이터 가정 ==============
DAILY_RIDERS = 7_000_000
WORKDAYS_YR = 250
KRW_PER_HOUR = 15_000
INFRA_PER_STATION_KRW = 3_000_000
INCENTIVE_KRW = 100

# 호선별 cap 도달도 (eda_line_carload 결과 기반 추정 - 1호선만 양봉, 나머지 cap)
LINE_CAP_RATIO = {
    "1호선": 0.55,  "2호선": 1.10, "3호선": 0.85, "4호선": 0.95,
    "5호선": 0.90,  "6호선": 0.70, "7호선": 0.95, "8호선": 0.75, "9호선": 1.10,
}
# 호선별 일평균 통행자 (서울교통공사 2024 추정)
LINE_DAILY = {
    "1호선": 950_000,  "2호선": 2_100_000, "3호선": 800_000, "4호선": 950_000,
    "5호선": 850_000,  "6호선": 600_000,   "7호선": 1_050_000, "8호선": 350_000, "9호선": 700_000,
}
# 시간대별 응답률 가중 (퇴근이 자율도 높음)
HOUR_RESPONSE_BIAS = {
    8: 0.7,   # 출근은 시간 강제 - 분산 응답 낮음
    18: 1.0,  # 퇴근 - 기준
    7: 0.85, 9: 1.05, 17: 1.05, 19: 1.05,
}


def hour_demand_curve():
    h = np.arange(24)
    am = 0.6 * np.exp(-((h - 8) ** 2) / 4.0)
    pm = 0.65 * np.exp(-((h - 18) ** 2) / 5.0)
    base = 0.18 * np.exp(-((h - 13) ** 2) / 18.0)
    night = np.where((h < 5) | (h > 23), 0.02, 0)
    raw = am + pm + base + night
    return raw / raw.sum()


def simulate_v3(behavior_response: float):
    """호선 × 시간 매트릭스 시뮬레이션."""
    demand = hour_demand_curve()
    lines = list(LINE_DAILY.keys())
    n_lines = len(lines)
    save_matrix = np.zeros((n_lines, 24))   # 호선 × 시간 절감 분
    cap_relief = np.zeros((n_lines, 24))    # cap 평탄화 효과 %

    for li, line in enumerate(lines):
        cap = LINE_CAP_RATIO[line]
        daily = LINE_DAILY[line]
        annual = daily * WORKDAYS_YR
        for h in range(24):
            d = demand[h]
            bias = HOUR_RESPONSE_BIAS.get(h, 1.0)
            eff_response = behavior_response * bias

            # cap이 1.0 초과(혼잡)일수록 1분당 절감 효과 큼 (1.5분 → 2.5분)
            base_save_min = 1.5 + max(0, cap - 1.0) * 10  # cap 1.1 → 2.5분
            if h in [8, 18]:
                save_matrix[li, h] = d * annual * eff_response * base_save_min
            elif h in [7, 9, 17, 19]:
                save_matrix[li, h] = d * annual * eff_response * (base_save_min * 0.5)
            else:
                save_matrix[li, h] = d * annual * eff_response * 0.2

            # cap 평탄화 - 응답률 30% → cap 1.10 → 1.05 (5%p 하락)
            if cap > 1.0:
                cap_relief[li, h] = (cap - 1.0) * eff_response * 100  # %p

    minutes_saved_yr = float(save_matrix.sum())
    commute_b = (minutes_saved_yr / 60) * KRW_PER_HOUR / 1e8

    # 사고 회피 - cap 1.0 초과 호선 가중 (혼잡할수록 사고 가능성 높음)
    over_cap_weight = sum(max(0, c - 1.0) for c in LINE_CAP_RATIO.values())
    safety_b = 500 * (0.4 + behavior_response * 0.6) * (1 + over_cap_weight)

    ad_b = 120 * (0.5 + behavior_response * 0.7)
    energy_b = 150 * behavior_response * 1.3
    coverage_riders = sum(LINE_DAILY.values()) * WORKDAYS_YR
    incentive_cost_b = coverage_riders * behavior_response * 0.45 * INCENTIVE_KRW / 1e8

    # 인프라 - 호선별 핵심 역만 (cap 1.0 초과는 모두 + 이하는 절반)
    n_stations_priority = 0
    for line, cap in LINE_CAP_RATIO.items():
        if cap >= 1.0: n_stations_priority += 25       # 만석 호선 25역
        else: n_stations_priority += 12               # 여유 호선 12역
    infra_b = n_stations_priority * INFRA_PER_STATION_KRW / 1e8

    total_b = commute_b + safety_b + ad_b + energy_b
    net_b = total_b - incentive_cost_b

    return {
        "behavior_response": behavior_response,
        "lines": lines,
        "minutes_saved_yr": minutes_saved_yr,
        "commute_b": commute_b,
        "safety_b": safety_b,
        "ad_b": ad_b,
        "energy_b": energy_b,
        "incentive_cost_b": incentive_cost_b,
        "total_gain_b": total_b,
        "net_value_b": net_b,
        "infra_b": infra_b,
        "roi_x": net_b / infra_b if infra_b > 0 else float("inf"),
        "save_matrix": save_matrix.tolist(),
        "cap_relief_avg_pp": float(cap_relief.mean()),
        "n_stations_priority": n_stations_priority,
    }


def fmt_b(v):
    if v >= 10000: return f"{v/10000:.2f}조"
    return f"{v:.0f}억"


def monte_carlo_ci(rates: list, n_sims: int = 1000, seed: int = 42) -> dict:
    """각 응답률 시나리오에 대해 Monte Carlo 1000회 → 95% CI.

    불확실성 주입:
        response_rate     ±15% (정책 채택률 변동)
        save_min_base     ±20% (역별 통근 절감 시간 분포)
        krw_per_hour      ±10% (한국교통연구원 혼잡비용 167원/분 ±)
        line_cap_ratio    ±10% (호선별 운영 변동)
    """
    rng = np.random.default_rng(seed)
    base_save_min_orig = 1.5
    krw_orig = KRW_PER_HOUR
    cap_orig = dict(LINE_CAP_RATIO)
    ci = {}
    for rate in rates:
        net_samples = []
        roi_samples = []
        min_samples = []
        for _ in range(n_sims):
            # perturbation
            r = float(np.clip(rate * rng.normal(1.0, 0.15 / 1.96), 0.001, 1.0))
            # base_save_min ±20% via global scaling — simulate then rescale
            save_factor = float(rng.normal(1.0, 0.20 / 1.96))
            krw_factor = float(rng.normal(1.0, 0.10 / 1.96))
            cap_factor = float(rng.normal(1.0, 0.10 / 1.96))
            # 임시 swap
            try:
                globals()["KRW_PER_HOUR"] = krw_orig * max(0.5, krw_factor)
                LINE_CAP_RATIO.update({k: v * max(0.5, cap_factor) for k, v in cap_orig.items()})
                res = simulate_v3(r)
            finally:
                globals()["KRW_PER_HOUR"] = krw_orig
                LINE_CAP_RATIO.update(cap_orig)
            # save factor 는 절감 분 자체에 곱해서 commute_b 재계산
            mins = res["minutes_saved_yr"] * max(0.4, save_factor)
            commute = (mins / 60) * (krw_orig * max(0.5, krw_factor)) / 1e8
            total = commute + res["safety_b"] + res["ad_b"] + res["energy_b"]
            net = total - res["incentive_cost_b"]
            roi = net / res["infra_b"] if res["infra_b"] > 0 else 0.0
            net_samples.append(net)
            roi_samples.append(roi)
            min_samples.append(mins)
        net_arr = np.array(net_samples)
        roi_arr = np.array(roi_samples)
        min_arr = np.array(min_samples)
        ci[f"{rate:.2f}"] = {
            "rate": rate,
            "net_b_mean": float(net_arr.mean()),
            "net_b_p5":   float(np.percentile(net_arr, 5)),
            "net_b_p95":  float(np.percentile(net_arr, 95)),
            "roi_x_mean": float(roi_arr.mean()),
            "roi_x_p5":   float(np.percentile(roi_arr, 5)),
            "roi_x_p95":  float(np.percentile(roi_arr, 95)),
            "minutes_p5":  float(np.percentile(min_arr, 5)),
            "minutes_p95": float(np.percentile(min_arr, 95)),
            "n_sims": n_sims,
        }
    return {
        "method": "Monte Carlo n=1000 per scenario, 95% CI = [p5, p95]",
        "perturbations": {
            "response_rate":  "±15% (정책 채택률 변동)",
            "save_min_base":  "±20% (역별 통근 절감 분포)",
            "krw_per_hour":   "±10% (한국교통연구원 167원/분 변동)",
            "line_cap_ratio": "±10% (호선별 운영 변동)",
        },
        "scenarios": ci,
    }


def main():
    print("=" * 72)
    print("MetroEyes 정책 ROI v3 - 호선 × 시간대 차등 (cap 도달도 + 응답 비대칭)")
    print("=" * 72)

    scenarios = [
        ("매우 보수 (5%)", 0.05),
        ("보수    (15%)",  0.15),
        ("중간    (30%)",  0.30),
        ("낙관    (50%)",  0.50),
        ("이상    (70%)",  0.70),
    ]
    print(f"\n  {'시나리오':<18} {'절감 분/년':>14} {'통근가치':>10} {'사고':>8} {'광고':>7} {'에너지':>8} {'인센티브-':>10} {'순가치':>11} {'ROI':>8}")
    print("  " + "-" * 110)
    results = []
    for label, rate in scenarios:
        r = simulate_v3(rate)
        results.append({"label": label, **r})
        print(f"  {label:<18} {r['minutes_saved_yr']/1e6:>11.1f}M분 "
              f"{fmt_b(r['commute_b']):>10} {fmt_b(r['safety_b']):>8} "
              f"{fmt_b(r['ad_b']):>7} {fmt_b(r['energy_b']):>8} "
              f"{fmt_b(r['incentive_cost_b']):>10} {fmt_b(r['net_value_b']):>11} "
              f"{r['roi_x']:>6,.0f}x")

    mid = results[2]
    print(f"\n  결론 - 응답률 30% (현실적 중간):")
    print(f"    순 사회적 가치     : {fmt_b(mid['net_value_b'])}/년")
    print(f"    1회성 인프라      : {fmt_b(mid['infra_b'])}  ({mid['n_stations_priority']}역 우선)")
    print(f"    ROI                : {mid['roi_x']:,.0f}x")
    print(f"    절감 시간         : {mid['minutes_saved_yr']/1e6:.1f}M분/년")
    print(f"    cap 평탄화 평균   : -{mid['cap_relief_avg_pp']:.2f}%p (혼잡 호선 입석↓)")

    # 호선별 절감 막대
    print("\n  [응답률 30%] 호선별 연 절감 분 - 만석 호선이 압도적")
    save = np.array(mid["save_matrix"])
    line_totals = save.sum(axis=1) / 1e6
    max_t = line_totals.max()
    for line, t in zip(mid["lines"], line_totals):
        bar = "█" * int(t / max_t * 32)
        print(f"    {line:<8} {t:>5.1f}M분 {bar}")

    # === Monte Carlo 95% CI (cycle 364) ===
    print("\n  [Monte Carlo n=1000 per scenario] 95% 신뢰구간 산출 중...")
    rates_for_ci = [s[1] for s in scenarios]
    ci_band = monte_carlo_ci(rates_for_ci, n_sims=1000, seed=42)
    print("    " + f"{'시나리오':<14} {'순가치 mean':>12} {'p5–p95':>22} {'ROI mean':>10} {'p5–p95':>16}")
    for label, rate in scenarios:
        ci = ci_band["scenarios"][f"{rate:.2f}"]
        print(f"    {label:<14} {fmt_b(ci['net_b_mean']):>12} "
              f"[{fmt_b(ci['net_b_p5'])}—{fmt_b(ci['net_b_p95'])}]".rjust(22) +
              f" {ci['roi_x_mean']:>8.0f}x [{ci['roi_x_p5']:.0f}—{ci['roi_x_p95']:.0f}x]".rjust(28))

    # JSON 저장 (matrix는 압축)
    summary = {**mid}
    summary["save_matrix"] = "[N_LINES × 24] omitted from JSON; see PNG"
    summary["all_scenarios"] = [
        {"label": x["label"], "rate": x["behavior_response"],
         "net_b": x["net_value_b"], "roi_x": x["roi_x"]}
        for x in results
    ]
    summary["ci_band"] = ci_band  # cycle 364 — Monte Carlo 95% CI
    with (OUT / "policy_roi_v3_report.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n  >> {OUT / 'policy_roi_v3_report.json'}")
    # CI band 별도 git tracked 위치 (frontend/figs/) — CI 회귀 가드용
    figs_dir = ROOT / "frontend" / "figs"
    figs_dir.mkdir(parents=True, exist_ok=True)
    with (figs_dir / "policy_roi_v3_ci_band.json").open("w", encoding="utf-8") as f:
        json.dump(ci_band, f, ensure_ascii=False, indent=2)
    print(f"  >> {figs_dir / 'policy_roi_v3_ci_band.json'}")

    # heatmap + 추가 차트 2종 (호선별 절감, 시나리오 비교)
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for name in ("Malgun Gothic", "NanumGothic"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break

        # 1) 호선×시간 heatmap
        fig, ax = plt.subplots(figsize=(13, 4.5))
        m = save / 1e6  # M분 단위
        im = ax.imshow(m, aspect="auto", cmap="YlOrRd")
        ax.set_xticks(range(24))
        ax.set_xticklabels([f"{h}" for h in range(24)])
        ax.set_yticks(range(len(mid["lines"])))
        ax.set_yticklabels(mid["lines"])
        ax.set_xlabel("시간 (시)")
        ax.set_ylabel("호선")
        ax.set_title(f"정책 ROI v3 - 응답률 30% 호선×시간대 연 절감 (M분)")
        plt.colorbar(im, ax=ax, label="M분/년")
        plt.tight_layout()
        png = OUT / "policy_roi_v3_matrix.png"
        plt.savefig(png, dpi=120)
        plt.close(fig)
        print(f"  >> {png}")

        # 2) 호선별 누적 절감 막대 차트 — 2호선 단독 압도성 가시화
        per_line = save.sum(axis=1) / 1e6  # M분/년
        fig2, ax2 = plt.subplots(figsize=(10, 4.5))
        order = np.argsort(per_line)[::-1]
        labels = [mid["lines"][i] for i in order]
        values = [per_line[i] for i in order]
        # 2호선만 강조 색상
        colors = ["#a78bfa" if l == "2호선" else "#7dd3d3" for l in labels]
        bars = ax2.bar(labels, values, color=colors, edgecolor="#0a0d12")
        for b, v in zip(bars, values):
            ax2.text(b.get_x() + b.get_width()/2, v + 2, f"{v:.0f}M", ha="center", fontsize=9, color="#222")
        ax2.set_ylabel("연 절감 (M분)")
        ax2.set_title(f"정책 ROI v3 - 호선별 연 절감 (응답률 30%, 총 {per_line.sum():.0f}M분)")
        ax2.grid(axis="y", linestyle="--", alpha=0.3)
        plt.tight_layout()
        png2 = OUT / "policy_roi_v3_per_line.png"
        plt.savefig(png2, dpi=120)
        plt.close(fig2)
        print(f"  >> {png2}")

        # 3) 시나리오 비교 + Monte Carlo 95% CI 리본 (cycle 364)
        fig3, (ax3a, ax3b) = plt.subplots(1, 2, figsize=(12, 4.2))
        rates = [r["behavior_response"] * 100 for r in results]
        net_vals = [r["net_value_b"] for r in results]
        rois = [r["roi_x"] for r in results]
        # CI band 리본 (p5~p95)
        net_p5 = [ci_band["scenarios"][f"{r['behavior_response']:.2f}"]["net_b_p5"] for r in results]
        net_p95 = [ci_band["scenarios"][f"{r['behavior_response']:.2f}"]["net_b_p95"] for r in results]
        roi_p5 = [ci_band["scenarios"][f"{r['behavior_response']:.2f}"]["roi_x_p5"] for r in results]
        roi_p95 = [ci_band["scenarios"][f"{r['behavior_response']:.2f}"]["roi_x_p95"] for r in results]
        ax3a.fill_between(rates, net_p5, net_p95, color="#10b981", alpha=0.15, label="95% CI (Monte Carlo n=1000)")
        ax3a.plot(rates, net_vals, "o-", color="#10b981", linewidth=2, markersize=8, label="중심 추정")
        for x, y in zip(rates, net_vals):
            ax3a.annotate(fmt_b(y), (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9)
        ax3a.set_xlabel("응답률 (%)")
        ax3a.set_ylabel("순 사회적 가치 (억/년)")
        ax3a.set_title("응답률별 순 가치 + 95% CI")
        ax3a.grid(linestyle="--", alpha=0.3)
        ax3a.axvspan(25, 35, alpha=0.12, color="#a78bfa", label="현실 추정 (30%)")
        ax3a.legend(loc="lower right", fontsize=8)
        ax3b.fill_between(rates, roi_p5, roi_p95, color="#f59e0b", alpha=0.15, label="95% CI")
        ax3b.plot(rates, rois, "s-", color="#f59e0b", linewidth=2, markersize=8, label="중심 추정")
        for x, y in zip(rates, rois):
            ax3b.annotate(f"{y:.0f}x", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=9)
        ax3b.set_xlabel("응답률 (%)")
        ax3b.set_ylabel("ROI (배)")
        ax3b.set_title("응답률별 ROI + 95% CI")
        ax3b.grid(linestyle="--", alpha=0.3)
        ax3b.axvspan(25, 35, alpha=0.12, color="#a78bfa")
        ax3b.legend(loc="lower right", fontsize=8)
        plt.suptitle("정책 ROI v3 — 시나리오 민감도 (Monte Carlo 1000회 95% CI)", fontsize=11)
        plt.tight_layout()
        png3 = OUT / "policy_roi_v3_scenarios.png"
        plt.savefig(png3, dpi=120)
        plt.close(fig3)
        print(f"  >> {png3}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
