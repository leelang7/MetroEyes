"""환승역 분석 EDA — 같은 STTN 다른 호선의 ON/OFF 비대칭 차이.

가설: 환승역에서 호선 간 ON/OFF 비대칭 차이 = 환승객 우세 방향.
예) 강남 2호선 09시 OFF/ON 12x vs 강남 신분당선 09시 OFF/ON 6x
    → 차이 6x = 신분당선 → 2호선 환승 출근객 우세

산출:
  outputs/transfer_stations.png — 환승역 호선 간 비대칭 차이 TOP 10
  outputs/transfer_stations_report.json
  frontend/figs/transfer_stations.png

활용 (pitch.html):
  분산 정책 우선순위 = 환승역 + 비대칭 차이 큰 곳 = 환승 흐름 변경 가능 지점.
  → 단일 호선 역보다 환승역 분산이 효과 ↑.
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
    print("MetroEyes EDA — 환승역 호선 간 비대칭 차이")
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

    am_h, pm_h = 9, 19
    g = df.groupby(["STTN", "SBWY_ROUT_LN_NM"]).agg(
        on_am=(f"HR_{am_h}_GET_ON_NOPE", "sum"),
        off_am=(f"HR_{am_h}_GET_OFF_NOPE", "sum"),
        on_pm=(f"HR_{pm_h}_GET_ON_NOPE", "sum"),
        off_pm=(f"HR_{pm_h}_GET_OFF_NOPE", "sum"),
    ).reset_index()

    # 환승역 = 같은 STTN 의 호선 수 ≥ 2
    line_count = g.groupby("STTN").size()
    transfer_sttns = line_count[line_count >= 2].index.tolist()
    print(f"[filter] 환승역 = {len(transfer_sttns)}개 (1~9호선 중)")

    # 환승역 별 호선 간 AM 비대칭 차이
    rows = []
    for sttn in transfer_sttns:
        sub = g[g["STTN"] == sttn].copy()
        if len(sub) < 2: continue
        # AM 비대칭 (OFF-ON)/(OFF+ON)
        sub["asym_am"] = (sub["off_am"] - sub["on_am"]) / (sub["off_am"] + sub["on_am"]).replace(0, 1)
        sub["asym_pm"] = (sub["off_pm"] - sub["on_pm"]) / (sub["off_pm"] + sub["on_pm"]).replace(0, 1)
        am_max, am_min = sub["asym_am"].max(), sub["asym_am"].min()
        pm_max, pm_min = sub["asym_pm"].max(), sub["asym_pm"].min()
        am_total = (sub["off_am"] + sub["on_am"]).sum()
        pm_total = (sub["off_pm"] + sub["on_pm"]).sum()
        am_diff = am_max - am_min
        pm_diff = pm_max - pm_min
        # 가장 비대칭이 큰 호선과 작은 호선 식별
        am_max_line = sub.loc[sub["asym_am"].idxmax(), "SBWY_ROUT_LN_NM"]
        am_min_line = sub.loc[sub["asym_am"].idxmin(), "SBWY_ROUT_LN_NM"]
        pm_max_line = sub.loc[sub["asym_pm"].idxmax(), "SBWY_ROUT_LN_NM"]
        pm_min_line = sub.loc[sub["asym_pm"].idxmin(), "SBWY_ROUT_LN_NM"]
        rows.append({
            "station": sttn,
            "n_lines": len(sub),
            "am_diff": am_diff,
            "am_total": am_total,
            "am_max_line": am_max_line, "am_max": am_max,
            "am_min_line": am_min_line, "am_min": am_min,
            "pm_diff": pm_diff,
            "pm_total": pm_total,
            "pm_max_line": pm_max_line, "pm_max": pm_max,
            "pm_min_line": pm_min_line, "pm_min": pm_min,
        })

    if not rows:
        print("[warn] 환승역 충분치 않음")
        return

    df_t = pd.DataFrame(rows)
    df_t = df_t[df_t["am_total"] >= 5000].copy()  # 통행량 5천+
    print(f"[filter] 통행량 5천+ 환승역 = {len(df_t)}")

    top_am = df_t.nlargest(10, "am_diff")
    top_pm = df_t.nlargest(10, "pm_diff")

    print(f"\n[AM 환승 비대칭 TOP 10] 09시 호선 간 OFF/ON 차이")
    for _, r in top_am.iterrows():
        print(f"  {r['station']:12s} n={int(r['n_lines'])}호선  "
              f"diff={r['am_diff']:.3f}  ({r['am_max_line']} {r['am_max']:+.2f} ↔ "
              f"{r['am_min_line']} {r['am_min']:+.2f})")

    print(f"\n[PM 환승 비대칭 TOP 10] 19시 호선 간 ON/OFF 차이")
    for _, r in top_pm.iterrows():
        print(f"  {r['station']:12s} n={int(r['n_lines'])}호선  "
              f"diff={r['pm_diff']:.3f}  ({r['pm_max_line']} {r['pm_max']:+.2f} ↔ "
              f"{r['pm_min_line']} {r['pm_min']:+.2f})")

    # plot
    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    am_lbls = [f"{r['station']}\n({r['am_max_line']} vs {r['am_min_line']})"
               for _, r in top_am.iterrows()]
    am_vals = top_am["am_diff"].values
    ax1.barh(range(len(am_vals)), am_vals, color="#ff5e57", alpha=0.85)
    ax1.set_yticks(range(len(am_vals)))
    ax1.set_yticklabels(am_lbls, fontsize=9)
    ax1.invert_yaxis()
    ax1.set_xlabel("호선 간 AM 비대칭 차이 -> 환승 흐름 우세", color="white")
    ax1.set_title(f"환승 우세 AM TOP 10 ({am_h}시)", color="white", fontsize=12)
    ax1.grid(alpha=0.1, axis="x")

    pm_lbls = [f"{r['station']}\n({r['pm_max_line']} vs {r['pm_min_line']})"
               for _, r in top_pm.iterrows()]
    pm_vals = top_pm["pm_diff"].values
    ax2.barh(range(len(pm_vals)), pm_vals, color="#10b981", alpha=0.85)
    ax2.set_yticks(range(len(pm_vals)))
    ax2.set_yticklabels(pm_lbls, fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlabel("호선 간 PM 비대칭 차이 -> 환승 흐름 우세", color="white")
    ax2.set_title(f"환승 우세 PM TOP 10 ({pm_h}시)", color="white", fontsize=12)
    ax2.grid(alpha=0.1, axis="x")

    fig.suptitle("MetroEyes EDA - 환승역 호선 간 비대칭 차이 (분산 정책 우선순위 후보)",
                 color="white", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "transfer_stations.png", dpi=130, bbox_inches="tight", facecolor="#04060a")
    plt.close(fig)
    print(f"\n[save] {OUT / 'transfer_stations.png'}")

    rep = {
        "am_hour": am_h, "pm_hour": pm_h,
        "n_transfer_stations": len(df_t),
        "top_am_diff": [
            {"station": r["station"], "n_lines": int(r["n_lines"]),
             "diff": float(r["am_diff"]),
             "max_line": r["am_max_line"], "max_asym": float(r["am_max"]),
             "min_line": r["am_min_line"], "min_asym": float(r["am_min"])}
            for _, r in top_am.iterrows()
        ],
        "top_pm_diff": [
            {"station": r["station"], "n_lines": int(r["n_lines"]),
             "diff": float(r["pm_diff"]),
             "max_line": r["pm_max_line"], "max_asym": float(r["pm_max"]),
             "min_line": r["pm_min_line"], "min_asym": float(r["pm_min"])}
            for _, r in top_pm.iterrows()
        ],
    }
    (OUT / "transfer_stations_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[save] {OUT / 'transfer_stations_report.json'}")


if __name__ == "__main__":
    main()
