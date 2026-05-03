"""정책 ROI 시뮬레이터 — MetroEyes 도입 시 연간 사회적 가치 추정.

발표 슬라이드 §4 표의 근거. 가정값을 바꿔가며 보수/낙관 시나리오 비교.
실행: python scripts/policy_roi.py [--optimistic | --conservative]
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass


@dataclass
class Assumptions:
    name: str
    daily_riders_m: float          # 일평균 통행 (백만)
    workdays_yr: int               # 연 근무일
    save_min_per_rider: float      # 1인당 통근시간 단축 (분)
    wage_krw_per_hour: int         # 시간당 임금 (원)
    crowd_incident_avoid_per_yr: float  # 회피 가능한 압사·사고 (건/년)
    crowd_incident_cost_b: float   # 1건당 사회적 비용 (억원)
    ad_market_b: float             # 지하철 광고 시장 (억원/년)
    ad_uplift_pct: float           # 시간차 가격 단가 인상 (%)
    metro_power_b: float           # 도시철도 전력비 (억원/년)
    energy_save_pct: float         # 칸 분산 → 공조 효율 (%)
    rollout_stations: int          # 배포 역수 (환승 허브 85)
    cost_per_station_m: float      # 1역당 인프라 비용 (백만원)


CONSERVATIVE = Assumptions(
    name="보수",
    daily_riders_m=7.0,
    workdays_yr=250,
    save_min_per_rider=2.0,
    wage_krw_per_hour=15_000,
    crowd_incident_avoid_per_yr=1.0,
    crowd_incident_cost_b=500.0,
    ad_market_b=2_000.0,
    ad_uplift_pct=5.0,
    metro_power_b=4_000.0,
    energy_save_pct=3.0,
    rollout_stations=85,
    cost_per_station_m=3.0,
)

OPTIMISTIC = Assumptions(
    name="낙관",
    daily_riders_m=7.5,
    workdays_yr=260,
    save_min_per_rider=4.0,
    wage_krw_per_hour=18_000,
    crowd_incident_avoid_per_yr=2.0,
    crowd_incident_cost_b=1_500.0,
    ad_market_b=2_500.0,
    ad_uplift_pct=8.0,
    metro_power_b=4_500.0,
    energy_save_pct=5.0,
    rollout_stations=181,  # 환승 허브 85 + 오피스형 96 일부
    cost_per_station_m=2.5,
)


def simulate(a: Assumptions) -> dict:
    # 1. 통근시간 단축 (억원/년)
    riders_yr = a.daily_riders_m * 1_000_000 * a.workdays_yr
    hours_saved = riders_yr * a.save_min_per_rider / 60
    commute_value = hours_saved * a.wage_krw_per_hour / 1e8  # 억원

    # 2. 사고 회피 (억원/년)
    safety_value = a.crowd_incident_avoid_per_yr * a.crowd_incident_cost_b

    # 3. 광고 단가 인상 (억원/년)
    ad_value = a.ad_market_b * a.ad_uplift_pct / 100

    # 4. 에너지 (억원/년)
    energy_value = a.metro_power_b * a.energy_save_pct / 100

    total_b = commute_value + safety_value + ad_value + energy_value
    cost_b = a.rollout_stations * a.cost_per_station_m / 100  # 백만→억
    payback_days = cost_b / total_b * 365 if total_b > 0 else float('inf')
    roi_x = total_b / cost_b if cost_b > 0 else float('inf')

    return {
        "commute": commute_value,
        "safety": safety_value,
        "ad": ad_value,
        "energy": energy_value,
        "total": total_b,
        "cost": cost_b,
        "payback_days": payback_days,
        "roi_multiple": roi_x,
    }


def fmt_b(x: float) -> str:
    """억 → 천억/조 단위 포맷."""
    if x >= 10_000:
        return f"{x/10_000:.2f}조"
    if x >= 1_000:
        return f"{x:.0f}억 ({x/10_000:.2f}조)"
    return f"{x:.0f}억"


def report(a: Assumptions, r: dict) -> None:
    print(f"\n=== {a.name} 시나리오 ===")
    print(f"  통근시간 단축    {fmt_b(r['commute']):>16}/년  "
          f"(1인당 -{a.save_min_per_rider}분 × 700만명 × 250일)")
    print(f"  사고 회피        {fmt_b(r['safety']):>16}/년  "
          f"({a.crowd_incident_avoid_per_yr}건 × {a.crowd_incident_cost_b}억)")
    print(f"  광고 단가 인상   {fmt_b(r['ad']):>16}/년  "
          f"(시장 {a.ad_market_b}억 × +{a.ad_uplift_pct}%)")
    print(f"  에너지 효율      {fmt_b(r['energy']):>16}/년  "
          f"(전력비 {a.metro_power_b}억 × -{a.energy_save_pct}%)")
    print(f"  ─────────────────────────────────────")
    print(f"  ▶ 연간 총 가치   {fmt_b(r['total']):>16}/년")
    print(f"  ▶ 1회성 인프라   {fmt_b(r['cost']):>16}    "
          f"({a.rollout_stations}역 × {a.cost_per_station_m}백만원)")
    print(f"  ▶ ROI            {r['roi_multiple']:>16,.0f}x")
    print(f"  ▶ 투자 회수      {r['payback_days']:>16.1f}일")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--optimistic", action="store_true")
    p.add_argument("--conservative", action="store_true")
    args = p.parse_args()

    print("MetroEyes 정책 ROI 시뮬레이터")
    print("=" * 60)

    if args.optimistic:
        report(OPTIMISTIC, simulate(OPTIMISTIC))
    elif args.conservative:
        report(CONSERVATIVE, simulate(CONSERVATIVE))
    else:
        for a in (CONSERVATIVE, OPTIMISTIC):
            report(a, simulate(a))
        print("\n" + "=" * 60)
        c, o = simulate(CONSERVATIVE), simulate(OPTIMISTIC)
        print(f"  레인지: {fmt_b(c['total'])} ~ {fmt_b(o['total'])} / 년")
        print(f"  ROI:   {c['roi_multiple']:.0f}x ~ {o['roi_multiple']:.0f}x")


if __name__ == "__main__":
    main()
