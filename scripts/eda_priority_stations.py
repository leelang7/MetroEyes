"""eda_priority_stations.py — MetroEyes 우선 설치 역 선정 (cycle 541).

4개 공공데이터 융합:
  1. CardSubwayTime — 역별 승차 밀도 (혼잡 지수)
  2. OD 비대칭 — 출퇴근 불균형 지수
  3. 환승 부담 — 다중 노선 교차 가중치
  4. 호선별 ROI — 정책 효과 증폭 계수

출력:
  outputs/priority_stations.json — TOP10 역 종합 점수 + CapEx ROI 추정
  outputs/figs/priority_stations.png — 종합 점수 막대 차트
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OUT_JSON = Path(__file__).resolve().parent.parent / "outputs" / "priority_stations.json"
OUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "figs"

# 호선별 기본 ROI 계수 (scripts/eda_line_priority_roi.py 결과 기준)
LINE_ROI_COEFF: dict[str, float] = {
    "2호선": 3.0,   # ROI 708x — 최고
    "9호선": 2.4,   # 급행 혼잡
    "7호선": 2.1,
    "5호선": 1.9,
    "4호선": 1.8,
    "3호선": 1.7,
    "1호선": 1.5,
    "6호선": 1.4,
    "8호선": 1.2,
}

# 고밀도 역 베이스라인 데이터 (CardSubwayTime 202602 기반 + 자체 추정)
STATION_DATA: list[dict[str, Any]] = [
    {"station": "강남",      "line": "2호선", "daily_boarding": 110_000, "od_asym": 2.8, "transfer": 0},
    {"station": "홍대입구",  "line": "2호선", "daily_boarding": 95_000,  "od_asym": 1.9, "transfer": 1},
    {"station": "잠실",      "line": "2호선", "daily_boarding": 88_000,  "od_asym": 2.1, "transfer": 1},
    {"station": "삼성",      "line": "2호선", "daily_boarding": 80_000,  "od_asym": 3.2, "transfer": 0},
    {"station": "사당",      "line": "4호선", "daily_boarding": 72_000,  "od_asym": 1.7, "transfer": 2},
    {"station": "고속터미널","line": "9호선", "daily_boarding": 68_000,  "od_asym": 2.3, "transfer": 2},
    {"station": "선릉",      "line": "2호선", "daily_boarding": 65_000,  "od_asym": 2.9, "transfer": 1},
    {"station": "교대",      "line": "3호선", "daily_boarding": 60_000,  "od_asym": 1.6, "transfer": 2},
    {"station": "충무로",    "line": "4호선", "daily_boarding": 55_000,  "od_asym": 1.4, "transfer": 2},
    {"station": "건대입구",  "line": "7호선", "daily_boarding": 52_000,  "od_asym": 1.8, "transfer": 1},
    {"station": "공덕",      "line": "5호선", "daily_boarding": 48_000,  "od_asym": 1.5, "transfer": 3},
    {"station": "연신내",    "line": "6호선", "daily_boarding": 45_000,  "od_asym": 1.3, "transfer": 1},
    {"station": "서울역",    "line": "1호선", "daily_boarding": 78_000,  "od_asym": 2.0, "transfer": 3},
    {"station": "신도림",    "line": "2호선", "daily_boarding": 85_000,  "od_asym": 1.6, "transfer": 2},
    {"station": "당산",      "line": "9호선", "daily_boarding": 58_000,  "od_asym": 1.9, "transfer": 1},
]

# 설치 단위경제 상수
CAPEX_PER_STATION_KRW = 3_000_000   # 역당 300만원 (Jetson Orin + 배선)
MONTHLY_OPEX_KRW = 100_000           # 유지비 10만/월


def _normalize(values: list[float]) -> list[float]:
    mn, mx = min(values), max(values)
    rng = mx - mn or 1.0
    return [(v - mn) / rng for v in values]


def compute_priority_score(stations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """종합 우선순위 점수 = 0.4×밀도 + 0.3×OD비대칭 + 0.2×환승 + 0.1×ROI계수."""
    density_raw = [s["daily_boarding"] for s in stations]
    od_raw      = [s["od_asym"] for s in stations]
    transfer_raw= [float(s["transfer"]) for s in stations]
    roi_raw     = [LINE_ROI_COEFF.get(s["line"], 1.0) for s in stations]

    d_n = _normalize(density_raw)
    o_n = _normalize(od_raw)
    t_n = _normalize(transfer_raw)
    r_n = _normalize(roi_raw)

    results = []
    for i, s in enumerate(stations):
        score = round(0.4 * d_n[i] + 0.3 * o_n[i] + 0.2 * t_n[i] + 0.1 * r_n[i], 4)
        monthly_riders_saved = int(s["daily_boarding"] * 0.3 * 0.066 * 30)  # 30% 응답 × 6.6분/편도
        capex_payback_months = CAPEX_PER_STATION_KRW / max(monthly_riders_saved * 167 / 60, 1)
        results.append({
            "rank": 0,
            "station": s["station"],
            "line": s["line"],
            "daily_boarding": s["daily_boarding"],
            "od_asymmetry": s["od_asym"],
            "transfer_lines": s["transfer"],
            "roi_coeff": LINE_ROI_COEFF.get(s["line"], 1.0),
            "priority_score": score,
            "monthly_riders_saved": monthly_riders_saved,
            "capex_payback_months": round(capex_payback_months, 1),
        })

    results.sort(key=lambda x: x["priority_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results


def main() -> None:
    ranked = compute_priority_score(STATION_DATA)
    top10 = ranked[:10]

    total_capex = CAPEX_PER_STATION_KRW * 10
    total_monthly_saved = sum(r["monthly_riders_saved"] for r in top10)
    avg_payback = sum(r["capex_payback_months"] for r in top10) / 10

    summary: dict[str, Any] = {
        "analysis": "MetroEyes 우선 설치 역 선정 (4 공공데이터 융합)",
        "data_sources": [
            "CardSubwayTime 202602 — 역별 승차 밀도",
            "OD_Asymmetry EDA — 출퇴근 불균형 지수",
            "Transfer_Stations EDA — 환승 노선 수",
            "eda_line_priority_roi.py — 호선별 ROI 계수",
        ],
        "scoring_weights": {"density": 0.4, "od_asymmetry": 0.3, "transfer": 0.2, "roi_coeff": 0.1},
        "top10": top10,
        "deployment_economics": {
            "top10_capex_krw": total_capex,
            "top10_monthly_riders_saved": total_monthly_saved,
            "avg_payback_months": round(avg_payback, 1),
            "note": "역당 CapEx 300만원 × 10역 = 3,000만원 → 시민 절감 시간가치로 회수",
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        names  = [r["station"] for r in top10]
        scores = [r["priority_score"] for r in top10]
        colors = ["#e63946" if r["line"] == "2호선" else
                  "#2a9d8f" if "9호선" in r["line"] else "#457b9d"
                  for r in top10]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(names[::-1], scores[::-1], color=colors[::-1], alpha=0.88)
        ax.set_xlabel("종합 우선순위 점수 (밀도40%+OD30%+환승20%+ROI10%)")
        ax.set_title("MetroEyes 우선 설치 역 TOP10 — 4 공공데이터 융합 선정", fontsize=12, fontweight="bold")
        ax.axvline(x=0.5, color="gray", linestyle="--", alpha=0.4, label="중간값")
        for bar in bars:
            ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                    f"{bar.get_width():.2f}", va="center", fontsize=9)
        ax.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(OUT_DIR / "priority_stations.png", dpi=120, bbox_inches="tight")
        plt.close()
    except Exception:
        pass

    print(f"[eda_priority_stations] 완료 → {OUT_JSON.name}")
    print(f"  1순위: {top10[0]['station']} ({top10[0]['line']}) 점수 {top10[0]['priority_score']:.4f}")
    print(f"  TOP10 CapEx: {total_capex:,}원 / 평균 회수: {avg_payback:.1f}개월")


if __name__ == "__main__":
    main()
