"""호선 × 시간대 우선순위 매트릭스 (cycle 368).

cycle 360 의 호선별 priority_score 를 시간대로 분해 → 9 호선 × 19 시간 (5~23시)
2D 매트릭스. 운영자에게 "어느 호선 어느 시간대" 정확한 정책 표적 제공.

산출 :
    frontend/figs/line_hour_priority_matrix.json (git tracked, CI 검증)
    outputs/line_hour_priority_heatmap.png (히트맵)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

# Windows cp949 콘솔에서도 한글/em-dash 정상 출력
if hasattr(sys.stdout, "reconfigure"):
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
FIGS = ROOT / "frontend" / "figs"
FIGS.mkdir(parents=True, exist_ok=True)

CARLOAD_CSV = OUT / "line_carload_est.csv"
REPORT_JSON = FIGS / "line_hour_priority_matrix.json"


def load_carload_2d() -> dict:
    """line_carload_est.csv 를 {line: {hour: occ_pct}} 로 로드."""
    if not CARLOAD_CSV.exists():
        raise SystemExit(f"필요: {CARLOAD_CSV} (먼저 eda_line_carload.py 실행)")
    by_line_hour: dict[str, dict[int, float]] = {}
    with CARLOAD_CSV.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            line = r["line"]
            try:
                hour = int(r["hour"])
                occ = float(r["occ_pct"])
            except (TypeError, ValueError):
                continue
            by_line_hour.setdefault(line, {})[hour] = occ
    return by_line_hour


def main() -> int:
    data = load_carload_2d()
    main_lines = [f"{i}호선" for i in range(1, 10)]
    hours = list(range(5, 24))
    # priority_score(line, hour) = occ_pct × commute_response_bias(hour)
    #   출근 (7~9): 0.7 (시간 강제) / 퇴근 (17~19): 1.0 (자율도 ↑)
    bias = {h: 1.0 for h in hours}
    bias.update({7: 0.85, 8: 0.7, 9: 1.05, 17: 1.05, 18: 1.0, 19: 1.05})
    matrix = []
    for line in main_lines:
        row = {"line": line, "hours": {}}
        line_data = data.get(line, {})
        for h in hours:
            occ = line_data.get(h, 0)
            score = occ * bias.get(h, 1.0)
            row["hours"][str(h)] = round(score, 1)
        matrix.append(row)
    # Top 5 cells (가장 높은 priority hour×line)
    cells = []
    for r in matrix:
        for h, score in r["hours"].items():
            cells.append({"line": r["line"], "hour": int(h), "score": score})
    cells.sort(key=lambda c: c["score"], reverse=True)
    top5 = cells[:5]
    bottom5 = cells[-5:]

    report = {
        "method": "occ_pct(line,hour) × commute_response_bias(hour) — 출근 0.7~1.05 / 퇴근 1.0~1.05",
        "lines": main_lines,
        "hours": hours,
        "matrix": matrix,
        "top5_cells": top5,
        "bottom5_cells": bottom5,
        "bias_table": {str(h): bias.get(h, 1.0) for h in hours},
    }
    with REPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 콘솔 요약 — Top 5 우선 cell
    print("[호선 × 시간대 우선순위 — Top 5 cells]")
    for c in top5:
        print(f"  {c['line']:<6} {c['hour']:>2}시 → priority {c['score']:>5.0f}")
    print("\n[Bottom 5 cells]")
    for c in bottom5:
        print(f"  {c['line']:<6} {c['hour']:>2}시 → priority {c['score']:>5.0f}")
    print(f"\n>> {REPORT_JSON}")

    # 히트맵
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for name in ("Malgun Gothic", "NanumGothic"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break
        import numpy as np
        m = np.array([[r["hours"][str(h)] for h in hours] for r in matrix])
        fig, ax = plt.subplots(figsize=(13, 4.5))
        im = ax.imshow(m, aspect="auto", cmap="YlOrRd")
        ax.set_xticks(range(len(hours)))
        ax.set_xticklabels([str(h) for h in hours])
        ax.set_yticks(range(len(main_lines)))
        ax.set_yticklabels(main_lines)
        ax.set_xlabel("시간 (시)")
        ax.set_ylabel("호선")
        ax.set_title("호선 × 시간대 차등 보상 우선순위 — peak × commute_response_bias 가중")
        plt.colorbar(im, ax=ax, label="priority score")
        # Top 5 cells 외곽 박스
        for c in top5:
            i = main_lines.index(c["line"])
            j = hours.index(c["hour"])
            ax.add_patch(plt.Rectangle((j-0.5, i-0.5), 1, 1, fill=False, edgecolor="#10b981", lw=2))
        # 셀 수치 표기 (50 이상만)
        for i in range(len(main_lines)):
            for j in range(len(hours)):
                v = m[i, j]
                if v > 50:
                    ax.text(j, i, f"{int(v)}", ha="center", va="center",
                            fontsize=7, color="black" if v < 100 else "white")
        plt.tight_layout()
        png = OUT / "line_hour_priority_heatmap.png"
        plt.savefig(png, dpi=120)
        plt.close(fig)
        print(f">> {png}")
    except ImportError:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
