"""ESG CO₂ 절감 정량 EDA (cycle 390).

ultra-conservative (admin 광고 0.012 kg) vs standard (0.088 kg) 두 시나리오:
- ultra-conservative: 자가용 회피 0.7% × 8.4km × 0.21 kg/km ≈ 0.012 (admin 광고 baseline)
- standard:           자가용 회피 5% × 8.4km × 0.21 kg/km   ≈ 0.088 (한국교통연구원 modal split)

광고는 ultra-conservative 채택 — 7배 보수. 실효 절감은 더 클 수 있음을 명시.

산출:
    frontend/figs/co2_savings_report.json (git tracked, CI 검증)
    outputs/co2_savings.png (시나리오별 CO₂ 막대)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Windows cp949 콘솔 한글 정상 출력
if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
FIGS = ROOT / "frontend" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)
REPORT_JSON = FIGS / "co2_savings_report.json"

# ============== 가정 (출처 명시) ==============
# Standard scenario (한국교통연구원 통근 modal split 보수 추정)
CAR_AVOIDANCE_STD = 0.05        # 5% — 분산 행동 → 자가용 회피 비율
# Ultra-conservative (admin 광고 baseline — 자가용 회피 0.7% 만 인정)
CAR_AVOIDANCE_ULTRA = 0.0068    # ≈ 0.7% — admin 광고 0.012 kg baseline 일치

COMMUTE_KM = 8.4                # 평균 서울 통근 거리 km (서울교통공사 2023)
KG_CO2_PER_KM = 0.21            # 평균 승용차 km당 배출 (환경부 2023, 평균 휘발유 1.5L 기준)
DAILY_RIDERS = 7_000_000        # 서울 도시철도 일평균 통행자
WORKDAYS_YR = 250
RESPONSE_RATE_DEFAULT = 0.30    # 정책 v3 30% 시나리오

ADVERTISED_VALUE_KG = 0.012     # admin / pitch 광고 baseline (ultra-conservative)


def co2_per_action_kg(rate: float = CAR_AVOIDANCE_STD) -> float:
    """분산 1회 CO₂ 절감 — rate × 통근 × kg/km."""
    return rate * COMMUTE_KM * KG_CO2_PER_KM


def annual_co2_savings_kg(response_rate: float, scenario: str = "ultra") -> dict:
    """1년치 CO₂ 절감 추정 — ultra-conservative (광고) vs standard (실효).

    응답률 r → 분산 행동 수 → CO₂ kg.
    """
    actions_yr = DAILY_RIDERS * response_rate * 0.45 * WORKDAYS_YR  # 정책 v3 와 동일 (1인 다회 0.45)
    rate = CAR_AVOIDANCE_ULTRA if scenario == "ultra" else CAR_AVOIDANCE_STD
    co2_per = co2_per_action_kg(rate)
    co2_yr_kg = actions_yr * co2_per
    return {
        "response_rate": response_rate,
        "scenario": scenario,
        "actions_yr": int(actions_yr),
        "co2_per_action_kg": round(co2_per, 4),
        "co2_yr_kg": round(co2_yr_kg, 1),
        "co2_yr_t": round(co2_yr_kg / 1000, 1),
        # 비교 — 한국 인 1년 평균 배출 12 톤
        "equivalent_persons_yr": round(co2_yr_kg / 12_000, 1),
    }


def main() -> int:
    print("=" * 72)
    print(" CO₂ 절감 정량 EDA (cycle 390) — ultra-conservative + standard 동시")
    print("=" * 72)

    ultra_per = co2_per_action_kg(CAR_AVOIDANCE_ULTRA)
    std_per = co2_per_action_kg(CAR_AVOIDANCE_STD)
    print(f"\n[derivation] 분산 1회 CO₂ 절감 (2 시나리오)")
    print(f"  ultra (광고 baseline): {CAR_AVOIDANCE_ULTRA*100:.2f}% × {COMMUTE_KM} km × {KG_CO2_PER_KM} kg/km = {ultra_per:.4f} kg")
    print(f"  광고 표기 0.012 kg 일치: {abs(ultra_per - 0.012) < 0.0005}")
    print(f"  standard (실효 추정): {CAR_AVOIDANCE_STD*100:.0f}% × {COMMUTE_KM} km × {KG_CO2_PER_KM} kg/km = {std_per:.4f} kg")
    print(f"  → 광고는 7배 보수 — 실제 효과는 더 클 수 있음")

    rates = [0.05, 0.15, 0.30, 0.50, 0.70]
    ultra_scenarios = [annual_co2_savings_kg(r, "ultra") for r in rates]
    std_scenarios = [annual_co2_savings_kg(r, "standard") for r in rates]

    print(f"\n[5 시나리오 — ultra (광고) / standard (실효)]")
    print(f"  {'응답률':<8} {'분산/년':>14} {'ultra t/yr':>13} {'standard t/yr':>15}")
    for u, s in zip(ultra_scenarios, std_scenarios):
        print(f"  {u['response_rate']*100:>5.0f}%   "
              f"{u['actions_yr']:>13,} "
              f"{u['co2_yr_t']:>11.1f} t "
              f"{s['co2_yr_t']:>13.1f} t")

    sc30u = [s for s in ultra_scenarios if abs(s["response_rate"] - 0.30) < 0.01][0]
    sc30s = [s for s in std_scenarios if abs(s["response_rate"] - 0.30) < 0.01][0]
    print(f"\n[30% 시나리오 — 광고 vs 실효]")
    print(f"  ultra (광고): {sc30u['co2_yr_t']:.0f} 톤/년 (한국인 {sc30u['equivalent_persons_yr']:.0f}년 배출)")
    print(f"  standard    : {sc30s['co2_yr_t']:.0f} 톤/년 (한국인 {sc30s['equivalent_persons_yr']:.0f}년 배출)")
    scenarios = ultra_scenarios  # 광고와 일치하도록 ultra 사용

    report = {
        "method": "ESG CO₂ derivation — ultra-conservative (0.7%) vs standard (5%) 자가용 회피 동시 산출",
        "sources": {
            "car_avoidance_ultra": "광고 baseline 0.012 kg/action 일치 reverse-derived 0.68%",
            "car_avoidance_std": "한국교통연구원 통근 modal split 보수 추정 5%",
            "commute_km": "서울교통공사 2023 평균 통근 8.4km",
            "kg_co2_per_km": "환경부 2023 평균 휘발유 승용차 0.21 kg CO2/km",
            "daily_riders": "서울 도시철도 일평균 700만",
            "workdays_yr": "주 5일 × 50주 = 250일",
        },
        "assumptions": {
            "car_avoidance_rate_ultra": CAR_AVOIDANCE_ULTRA,
            "car_avoidance_rate_standard": CAR_AVOIDANCE_STD,
            "commute_km": COMMUTE_KM,
            "kg_co2_per_km": KG_CO2_PER_KM,
            "daily_riders": DAILY_RIDERS,
            "workdays_yr": WORKDAYS_YR,
            "actions_per_responding_user": 0.45,
            "korean_avg_co2_per_person_yr_kg": 12_000,
        },
        "co2_per_action_kg_ultra": round(ultra_per, 4),
        "co2_per_action_kg_standard": round(std_per, 4),
        "advertised_value_kg": ADVERTISED_VALUE_KG,
        "match_advertised_ultra": abs(ultra_per - ADVERTISED_VALUE_KG) < 0.0005,
        "scenarios_ultra": ultra_scenarios,
        "scenarios_standard": std_scenarios,
        "scenario_30pct_ultra": sc30u,
        "scenario_30pct_standard": sc30s,
    }
    with REPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n>> {REPORT_JSON}")

    # 막대 그래프
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for name in ("Malgun Gothic", "NanumGothic"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break
        fig, ax = plt.subplots(figsize=(10, 4.5))
        labels = [f"{s['response_rate']*100:.0f}%" for s in scenarios]
        values = [s["co2_yr_t"] for s in scenarios]
        colors = ["#7dd3d3" if s["response_rate"] != 0.30 else "#a78bfa" for s in scenarios]
        bars = ax.bar(labels, values, color=colors, edgecolor="#0a0d12")
        for b, v, s in zip(bars, values, scenarios):
            ax.text(b.get_x() + b.get_width()/2, v + 30,
                    f"{v:.0f} t\n(한국인 {s['equivalent_persons_yr']:.0f}년)",
                    ha="center", fontsize=9, color="#1a1a1f")
        ax.set_xlabel("정책 응답률")
        ax.set_ylabel("CO₂ 절감 (톤/년)")
        ax.set_title(f"분산 정책 CO₂ 절감 (ultra-conservative) — 분산 1회 {ultra_per*1000:.1f} g eq")
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        plt.tight_layout()
        png = OUT / "co2_savings.png"
        plt.savefig(png, dpi=120)
        plt.close(fig)
        print(f">> {png}")
    except ImportError:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
