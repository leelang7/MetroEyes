"""ON/OFF 비대칭 EDA — 출근 도착지 vs 출발지 식별.

가설: 09시 강남역은 OFF >> ON (출근 도착지). 19시 강남역은 ON >> OFF (퇴근 출발지).
역×시간대 비대칭(ON-OFF)/(ON+OFF) 지수로 정량 식별 → 정책 우선순위 인사이트.

산출:
  outputs/od_asymmetry.png        — 출근 도착 TOP 10 + 퇴근 출발 TOP 10 막대그래프
  outputs/od_asymmetry_report.json — 정량 리포트
  frontend/figs/od_asymmetry.png   — pitch.html figure 4 용 복사

활용 (pitch.html):
  분산 정책 우선순위 = OFF >> ON 인 역의 도착 시간대에 인센티브 집중.
  → 인프라 4억 / 134역 우선 모델의 *근거*를 한눈에.
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


def main():
    print("=" * 72)
    print("MetroEyes EDA — ON/OFF 비대칭 TOP 10")
    print("=" * 72)
    if not DATA.exists():
        raise SystemExit(f"데이터 없음: {DATA}")
    try:
        import pandas as pd
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
    except ImportError as e:
        raise SystemExit(f"필수 패키지 없음: {e}")

    candidates = ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans KR"]
    available = {f.name for f in fm.fontManager.ttflist}
    chosen = next((c for c in candidates if c in available), None)
    if chosen:
        plt.rcParams["font.family"] = chosen
        plt.rcParams["axes.unicode_minus"] = False
        print(f"[font] {chosen}")

    df = pd.read_parquet(DATA)
    main_lines = [f"{i}호선" for i in range(1, 10)]
    df = df[df["SBWY_ROUT_LN_NM"].isin(main_lines)].copy()
    print(f"[load] {len(df):,}행 / 1~9호선")

    # 역명별 28일 합계 → 09시 ON/OFF, 19시 ON/OFF
    am_h, pm_h = 9, 19
    on_am = f"HR_{am_h}_GET_ON_NOPE"
    off_am = f"HR_{am_h}_GET_OFF_NOPE"
    on_pm = f"HR_{pm_h}_GET_ON_NOPE"
    off_pm = f"HR_{pm_h}_GET_OFF_NOPE"

    # 역명 + 호선별 합계 (같은 역명 다른 호선 환승역은 분리)
    g = df.groupby(["STTN", "SBWY_ROUT_LN_NM"]).agg(
        on_am_sum=(on_am, "sum"),
        off_am_sum=(off_am, "sum"),
        on_pm_sum=(on_pm, "sum"),
        off_pm_sum=(off_pm, "sum"),
    ).reset_index()
    print(f"[agg] {len(g)} 역×호선 entry")

    # 비대칭 지수
    def asym(on, off):
        s = on + off
        return (off - on) / s if s > 0 else 0   # OFF가 많으면 양수 (출근 도착)

    g["asym_am"] = g.apply(lambda r: asym(r["on_am_sum"], r["off_am_sum"]), axis=1)
    g["asym_pm"] = g.apply(lambda r: asym(r["on_pm_sum"], r["off_pm_sum"]), axis=1)
    g["total_am"] = g["on_am_sum"] + g["off_am_sum"]
    g["total_pm"] = g["on_pm_sum"] + g["off_pm_sum"]

    # 의미있는 역만 — top quantile (총 통행량 상위 70% 누적)
    threshold = max(g["total_am"].quantile(0.30), g["total_pm"].quantile(0.30), 5000)
    sig = g[(g["total_am"] >= threshold) & (g["total_pm"] >= threshold)].copy()
    print(f"[filter] 통행량 {threshold:.0f}+ 역×호선 = {len(sig)}")

    # TOP 10 출근 도착지 (asym_am 가장 양수)
    top_arr = sig.nlargest(10, "asym_am")[["STTN", "SBWY_ROUT_LN_NM", "asym_am",
                                           "on_am_sum", "off_am_sum", "total_am"]].copy()
    # TOP 10 퇴근 출발지 (asym_pm 가장 음수 — ON이 많은)
    top_dep = sig.nsmallest(10, "asym_pm")[["STTN", "SBWY_ROUT_LN_NM", "asym_pm",
                                            "on_pm_sum", "off_pm_sum", "total_pm"]].copy()

    print("\n[출근 도착 TOP 10] 09시 OFF >> ON")
    for _, r in top_arr.iterrows():
        ratio = r["off_am_sum"] / r["on_am_sum"] if r["on_am_sum"] > 0 else 0
        print(f"  {r['STTN']:8s} ({r['SBWY_ROUT_LN_NM']}) "
              f"asym={r['asym_am']:+.3f}  OFF/ON={ratio:.1f}x  총 {r['total_am']/1e3:.0f}천명")
    print("\n[퇴근 출발 TOP 10] 19시 ON >> OFF")
    for _, r in top_dep.iterrows():
        ratio = r["on_pm_sum"] / r["off_pm_sum"] if r["off_pm_sum"] > 0 else 0
        print(f"  {r['STTN']:8s} ({r['SBWY_ROUT_LN_NM']}) "
              f"asym={r['asym_pm']:+.3f}  ON/OFF={ratio:.1f}x  총 {r['total_pm']/1e3:.0f}천명")

    # plot
    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    # 출근 도착 — 빨강
    arr_lbls = [f"{r['STTN']}\n({r['SBWY_ROUT_LN_NM']})" for _, r in top_arr.iterrows()]
    arr_vals = top_arr["asym_am"].values
    ax1.barh(range(len(arr_vals)), arr_vals, color="#ff5e57", alpha=0.85)
    ax1.set_yticks(range(len(arr_vals)))
    ax1.set_yticklabels(arr_lbls, fontsize=9)
    ax1.invert_yaxis()
    ax1.set_xlabel("(OFF - ON) / 총합 -> 클수록 출근 도착지", color="white")
    ax1.set_title(f"출근 도착 TOP 10 ({am_h}시 OFF >> ON)", color="white", fontsize=12)
    ax1.grid(alpha=0.1, axis="x")
    for i, v in enumerate(arr_vals):
        ax1.text(v + 0.01, i, f"{v:+.2f}", va="center", color="#ff5e57", fontsize=8)

    # 퇴근 출발 — 초록
    dep_lbls = [f"{r['STTN']}\n({r['SBWY_ROUT_LN_NM']})" for _, r in top_dep.iterrows()]
    dep_vals = top_dep["asym_pm"].values
    ax2.barh(range(len(dep_vals)), dep_vals, color="#10b981", alpha=0.85)
    ax2.set_yticks(range(len(dep_vals)))
    ax2.set_yticklabels(dep_lbls, fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlabel("(OFF - ON) / 총합 -> 작을수록 퇴근 출발지", color="white")
    ax2.set_title(f"퇴근 출발 TOP 10 ({pm_h}시 ON >> OFF)", color="white", fontsize=12)
    ax2.grid(alpha=0.1, axis="x")
    for i, v in enumerate(dep_vals):
        ax2.text(v - 0.01, i, f"{v:+.2f}", va="center", ha="right", color="#10b981", fontsize=8)

    fig.suptitle("MetroEyes EDA - 출퇴근 OD 비대칭 (1~9호선 28일 평균)", color="white", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "od_asymmetry.png", dpi=130, bbox_inches="tight", facecolor="#04060a")
    plt.close(fig)
    print(f"\n[save] {OUT / 'od_asymmetry.png'}")

    # JSON
    rep = {
        "am_hour": am_h,
        "pm_hour": pm_h,
        "min_total_threshold": float(threshold),
        "top_arrival": [
            {"station": r["STTN"], "line": r["SBWY_ROUT_LN_NM"], "asym": float(r["asym_am"]),
             "on": int(r["on_am_sum"]), "off": int(r["off_am_sum"])}
            for _, r in top_arr.iterrows()
        ],
        "top_departure": [
            {"station": r["STTN"], "line": r["SBWY_ROUT_LN_NM"], "asym": float(r["asym_pm"]),
             "on": int(r["on_pm_sum"]), "off": int(r["off_pm_sum"])}
            for _, r in top_dep.iterrows()
        ],
        "n_significant_stations": len(sig),
    }
    (OUT / "od_asymmetry_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[save] {OUT / 'od_asymmetry_report.json'}")
    print("\n[done] OD 비대칭 EDA 완료")


if __name__ == "__main__":
    main()
