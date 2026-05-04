"""분산 운임 인센티브 정책 - 행동 확률 + 시간대 + 환승허브 우선 시뮬.

policy_roi.py 의 단순 보수/낙관에서 한 단계 진화:
  - 시간대별 통행량 가중 (8시 / 18시 양봉)
  - 환승허브 85역 (silhouette 0.387) 우선 적용
  - 인센티브 행동 변환율 5단계 (얼마나 분산 응답할지)
  - 시뮬 1년 = 250 영업일 × 24시간 슬롯 적분
  - 민감도 분석 (parameter sweep)

산출:
  outputs/policy_roi_v2_report.json
  outputs/policy_roi_v2_curve.png
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


# ============== 데이터 가정 (출처 표기) ==============
# 서울교통공사 2024 통계
DAILY_RIDERS = 7_000_000          # 도시철도 일평균 통행
WORKDAYS_YR = 250
HUB_STATIONS = 85                  # K=3 클러스터 환승허브

# 1주차 EDA 결과
PEAK_RATIO = 1.9                   # 피크/한산 시간대 진폭
PEAK_HOURS = [8, 18]               # 출퇴근 양봉

# 사회적 비용 가정
KRW_PER_HOUR = 15_000              # 시간당 임금 (한국 평균)
INFRA_PER_STATION_KRW = 3_000_000  # 1역당 카메라 4대 + Jetson Orin Nano

# 인센티브 정책 파라미터
INCENTIVE_KRW = 100                # 분산 시 차감 1회
PEAK_WINDOW_MIN = 15               # 분산 윈도우 (8:30-8:45 등)


def hour_demand_curve():
    """24시간 통행 밀도 - 양봉 + 평탄 + 노이즈."""
    h = np.arange(24)
    am = 0.6 * np.exp(-((h - 8) ** 2) / 4.0)
    pm = 0.65 * np.exp(-((h - 18) ** 2) / 5.0)
    base = 0.18 * np.exp(-((h - 13) ** 2) / 18.0)
    night = np.where((h < 5) | (h > 23), 0.02, 0)
    raw = am + pm + base + night
    return raw / raw.sum()  # 1로 정규화


def simulate(behavior_response: float, hub_focus: float = 1.0):
    """
    behavior_response : 0.0~1.0 - 인센티브에 응답해 분산하는 통행자 비율
    hub_focus         : 1.0 = 환승허브 85역만, 296 = 모든 역
    """
    demand = hour_demand_curve()
    annual_riders = DAILY_RIDERS * WORKDAYS_YR  # ~17.5억
    # 적용 모집단 - 환승허브 비율 (85/296)
    coverage_ratio = HUB_STATIONS / 296.0 if hub_focus == 1.0 else min(1.0, hub_focus / 296.0)

    # 시간대별 절감 분 (피크에서만 분산 효과)
    minutes_saved = 0.0
    for h in range(24):
        peak_factor = max(0, (demand[h] - demand.min()) / (demand.max() - demand.min()))
        if h in PEAK_HOURS:
            # 피크 시간 분산 효과 = 응답률 × 1.5분 평균 절감
            minutes_saved += demand[h] * annual_riders * coverage_ratio * behavior_response * 1.5
        elif h in [7, 9, 17, 19]:  # 인접 시간
            minutes_saved += demand[h] * annual_riders * coverage_ratio * behavior_response * 0.7

    # 통근시간 단축 가치
    commute_value_b = (minutes_saved / 60) * KRW_PER_HOUR / 1e8  # 억원

    # 사고 회피 - 응답률 비례 + base
    safety_value_b = 500 * (0.5 + behavior_response * 0.5) * coverage_ratio

    # 광고 단가 인상 (분산이 광고 노출 시간 분산도 만듦)
    ad_value_b = 100 * coverage_ratio * (0.5 + behavior_response * 0.7)

    # 에너지 (공조/조명 분산)
    energy_value_b = 120 * coverage_ratio * behavior_response * 1.2

    # 인센티브 지급 비용 (정책 운영 cost)
    incentive_count = annual_riders * coverage_ratio * behavior_response * 0.4  # 40% 이중 적용
    incentive_cost_b = incentive_count * INCENTIVE_KRW / 1e8  # 억원

    total_b = commute_value_b + safety_value_b + ad_value_b + energy_value_b
    net_b = total_b - incentive_cost_b
    infra_b = HUB_STATIONS * INFRA_PER_STATION_KRW / 1e8  # 2.55억 (보수)
    if hub_focus > 1.0:
        infra_b = (HUB_STATIONS + (296 - HUB_STATIONS) * (hub_focus - 1.0) / 211) * INFRA_PER_STATION_KRW / 1e8

    return {
        "behavior_response": behavior_response,
        "coverage_ratio": coverage_ratio,
        "commute_b": commute_value_b,
        "safety_b": safety_value_b,
        "ad_b": ad_value_b,
        "energy_b": energy_value_b,
        "incentive_cost_b": incentive_cost_b,
        "total_gain_b": total_b,
        "net_value_b": net_b,
        "infra_b": infra_b,
        "roi_x": net_b / infra_b if infra_b > 0 else float("inf"),
        "minutes_saved_yr": minutes_saved,
    }


def fmt_b(v):
    if v >= 10000: return f"{v/10000:.2f}조"
    return f"{v:.0f}억"


def main():
    print("=" * 68)
    print("MetroEyes 분산 운임 인센티브 정책 - ROI v2 (행동 확률 + 시간대)")
    print("=" * 68)

    # 시나리오 5단계 - 응답률
    scenarios = [
        ("매우 보수 (5%)",  0.05),
        ("보수    (15%)",   0.15),
        ("중간    (30%)",   0.30),
        ("낙관    (50%)",   0.50),
        ("이상    (70%)",   0.70),
    ]
    print(f"\n  {'시나리오':<18} {'통근절감':>10} {'사고':>8} {'광고':>8} {'에너지':>8} {'인센티브-':>10} {'순가치':>11} {'ROI':>8}")
    print("  " + "-" * 90)
    results = []
    for label, rate in scenarios:
        r = simulate(rate)
        results.append({"label": label, **r})
        print(f"  {label:<18} {fmt_b(r['commute_b']):>10} {fmt_b(r['safety_b']):>8} "
              f"{fmt_b(r['ad_b']):>8} {fmt_b(r['energy_b']):>8} "
              f"{fmt_b(r['incentive_cost_b']):>10} {fmt_b(r['net_value_b']):>11} {r['roi_x']:>6,.0f}x")

    print(f"\n  결론 - 응답률 30% (현실적 중간) 가정 시:")
    mid = results[2]
    print(f"    순 사회적 가치 : {fmt_b(mid['net_value_b'])}/년")
    print(f"    1회성 인프라   : {fmt_b(mid['infra_b'])}")
    print(f"    ROI            : {mid['roi_x']:,.0f}x")
    print(f"    절감 시간      : {mid['minutes_saved_yr']/1e6:.0f}백만 분/년")

    # 민감도 (응답률 vs 순가치)
    print("\n" + "=" * 68)
    print("  민감도 분석 - 응답률 0~80% 그래프")
    print("=" * 68)
    rates = np.linspace(0, 0.80, 17)
    nets = [simulate(r)["net_value_b"] for r in rates]

    # ASCII 차트
    max_v = max(nets)
    for i, (r, n) in enumerate(zip(rates, nets)):
        bar = int(n / max_v * 40) if max_v > 0 else 0
        print(f"  {r*100:>5.0f}%  {fmt_b(n):>10}  {'#' * bar}")

    # JSON 산출
    report = {
        "scenarios": results,
        "sensitivity": [{"response": float(r), "net_b": float(n)} for r, n in zip(rates, nets)],
        "assumptions": {
            "daily_riders": DAILY_RIDERS,
            "workdays_yr": WORKDAYS_YR,
            "hub_stations": HUB_STATIONS,
            "krw_per_hour": KRW_PER_HOUR,
            "infra_per_station": INFRA_PER_STATION_KRW,
            "incentive_krw": INCENTIVE_KRW,
        },
    }
    out_json = OUT / "policy_roi_v2_report.json"
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  [OK] {out_json}")

    # matplotlib 그래프 (있으면)
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for name in ("Malgun Gothic", "NanumGothic"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(rates * 100, nets, marker="o", linewidth=2, color="#c33764")
        ax.fill_between(rates * 100, 0, nets, alpha=0.15, color="#c33764")
        ax.set_xlabel("인센티브 응답률 (%)")
        ax.set_ylabel("순 사회적 가치 (억원/년)")
        ax.set_title("MetroEyes 분산 운임 정책 - 응답률 민감도")
        ax.grid(alpha=0.3)
        for x_target in [15, 30, 50]:
            arr = (rates * 100).round().astype(int)
            idxs = np.where(arr == x_target)[0]
            if len(idxs):
                i = int(idxs[0])
                ax.annotate(f"{fmt_b(nets[i])}",
                            xy=(x_target, nets[i]),
                            xytext=(x_target+2, nets[i]+30),
                            fontsize=9, color="#1d3557")
        plt.tight_layout()
        png_path = OUT / "policy_roi_v2_curve.png"
        plt.savefig(png_path, dpi=120)
        print(f"  [OK] {png_path}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
