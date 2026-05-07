"""호선별 차등 보상 ROI 시뮬레이션 (cycle 360).

기존 line_carload_est.csv (호선 × 시간대 점유율 추정) 와 policy_roi_v3 의
saved_minutes_matrix 를 결합 → 호선별 분산 보상 우선 배정 시 ROI 계산.

질문에 답: "₩400M 한정 예산을 9개 호선에 어떻게 배분해야 ROI 최대?"

산출:
  outputs/line_priority_roi.csv      — 호선별 ROI 순위
  outputs/line_priority_roi.png      — 가로 막대 (호선 × ROI)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
FIGS = ROOT / "frontend" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)

CARLOAD_CSV = OUT / "line_carload_est.csv"
ROI_JSON = OUT / "policy_roi_v3_report.json"
# 회귀 테스트용 — git tracked
REPORT_JSON = FIGS / "line_priority_roi_report.json"


def load_carload() -> dict:
    """호선별 평균 점유율, 피크 점유율, 100% 초과 시간대 수 산출."""
    if not CARLOAD_CSV.exists():
        raise SystemExit(f"필요: {CARLOAD_CSV} (먼저 eda_line_carload.py 실행)")
    by_line: dict[str, list[float]] = {}
    with CARLOAD_CSV.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        line = r["line"]
        try:
            occ = float(r["occ_pct"])
        except (TypeError, ValueError):
            continue
        by_line.setdefault(line, []).append(occ)
    summary = {}
    for line, occs in by_line.items():
        if not occs:
            continue
        avg = sum(occs) / len(occs)
        peak = max(occs)
        over_100 = sum(1 for v in occs if v >= 100)
        summary[line] = {"avg_pct": avg, "peak_pct": peak, "over_100_hours": over_100}
    return summary


def load_roi_per_line() -> dict:
    """호선별 연간 saved minutes — 정책 ROI v3 직접 시뮬 결과 (per_line_saved_min).

    cycle 374 fix: 이전에는 line_carload on_total 비중으로 분배했으나
    광고 "2호선 단독 157M" 와 충돌. 정책 v3 가 source of truth.
    """
    if ROI_JSON.exists():
        try:
            d = json.loads(ROI_JSON.read_text(encoding="utf-8"))
            per_line = d.get("per_line_saved_min")
            if per_line:
                return per_line
        except Exception:
            pass
    # fallback (정책 v3 안 돌렸으면) — line_carload 비중 분배
    if not CARLOAD_CSV.exists():
        return {f"{i}호선": 17_000_000 for i in range(1, 10)}
    by_line: dict[str, float] = {}
    with CARLOAD_CSV.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            line = r["line"]
            try:
                on = float(r["on_total"])
            except (TypeError, ValueError):
                continue
            by_line[line] = by_line.get(line, 0) + on
    total_saved_yr = 473_400_000
    main_lines = {f"{i}호선" for i in range(1, 10)}
    main_total = sum(v for k, v in by_line.items() if k in main_lines)
    if main_total <= 0:
        return {f"{i}호선": int(total_saved_yr / 9) for i in range(1, 10)}
    return {line: int(on / main_total * total_saved_yr)
            for line, on in by_line.items() if line in main_lines}


def main() -> int:
    cl = load_carload()
    saved = load_roi_per_line()
    # 9개 핵심 호선만
    main_lines = [f"{i}호선" for i in range(1, 10)]
    rows = []
    for line in main_lines:
        c = cl.get(line, {"avg_pct": 0, "peak_pct": 0, "over_100_hours": 0})
        sm = saved.get(line, 0)
        # 우선도 점수: peak × over_100 가중 (피크 부담 큰 호선이 분산 효과 큼)
        priority = c["peak_pct"] * (1 + c["over_100_hours"] * 0.3)
        # ROI: 분당 사회적 가치 ₩200 가정 (정책 v3 와 동일)
        won_per_min = 200
        social_value = sm * won_per_min
        # 가상 예산 배분: 균등 ₩400M / 9 = ₩44.4M 호선
        line_budget = 400_000_000 / 9
        roi = social_value / line_budget if line_budget > 0 else 0
        rows.append({
            "line": line,
            "avg_pct": round(c["avg_pct"], 1),
            "peak_pct": round(c["peak_pct"], 1),
            "over_100_hours": c["over_100_hours"],
            "saved_min_yr": int(sm),
            "social_value_won": int(social_value),
            "priority_score": round(priority, 1),
            "roi_x": round(roi, 1),
        })
    # 우선도 점수로 정렬
    rows.sort(key=lambda r: r["priority_score"], reverse=True)

    csv_out = OUT / "line_priority_roi.csv"
    with csv_out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    # JSON 리포트 — frontend/figs/ 에 git tracked (CI 회귀 테스트용)
    report = {
        "lines": rows,
        "total_saved_min_yr": sum(r["saved_min_yr"] for r in rows),
        "total_social_value_won": sum(r["social_value_won"] for r in rows),
        "budget_per_line_won": int(400_000_000 / 9),
        "response_rate": 0.30,
        "won_per_min": 200,
        "method": "line_carload_est on_total 비중 × policy_roi_v3 30% 시나리오 473.4M/년",
    }
    with REPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n>> {REPORT_JSON}")

    print("[호선별 차등 보상 우선순위 (peak × over_100 가중)]")
    print(f"{'호선':<6} {'평균':>5} {'피크':>5} {'>100h':>6} {'우선도':>6} {'절감분/년':>11} {'사회가치':>11} {'ROI':>5}")
    for r in rows:
        sv_b = r["social_value_won"] / 100_000_000  # 억
        sm_m = r["saved_min_yr"] / 1_000_000  # 백만분
        print(f"{r['line']:<6} {r['avg_pct']:>4.0f}% {r['peak_pct']:>4.0f}% "
              f"{r['over_100_hours']:>5d}h {r['priority_score']:>5.0f} "
              f"{sm_m:>9.1f}M {sv_b:>9.1f}억 {r['roi_x']:>4.0f}x")
    print(f"\n>> {csv_out}")

    # 가로 막대 그래프
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for name in ("Malgun Gothic", "NanumGothic"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        # left: priority score
        ax1 = axes[0]
        lines = [r["line"] for r in rows]
        scores = [r["priority_score"] for r in rows]
        ax1.barh(lines, scores, color="#a78bfa")
        ax1.set_xlabel("우선도 점수 (peak × over-100 가중)")
        ax1.set_title("호선별 분산 보상 우선순위")
        ax1.invert_yaxis()
        for i, s in enumerate(scores):
            ax1.text(s + 1, i, f"{s:.0f}", va="center", fontsize=9)
        # right: ROI
        ax2 = axes[1]
        rois = [r["roi_x"] for r in rows]
        ax2.barh(lines, rois, color="#7dd3d3")
        ax2.set_xlabel("ROI x (₩400M ÷ 9 호선 균등 배분 기준)")
        ax2.set_title("호선별 ROI — 같은 예산 시 효율 차이")
        ax2.invert_yaxis()
        for i, v in enumerate(rois):
            ax2.text(v + 5, i, f"{v:.0f}x", va="center", fontsize=9)
        plt.suptitle("호선별 차등 보상 ROI 시뮬레이션 — 1주차 EDA + 정책 ROI v3 결합", fontsize=12)
        plt.tight_layout()
        png = OUT / "line_priority_roi.png"
        plt.savefig(png, dpi=120)
        print(f">> {png}")
    except ImportError:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
