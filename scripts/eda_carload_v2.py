"""호선 × 시간 점유 추정 v2 - 외부 특성 결합 GBR 회귀.

v1 (eda_line_carload.py) 한계:
  - 점유율은 단순 ON/cars/cap 비율
  - 호선 cap 도달도, 시간대 양봉, 환승역 비대칭 모두 별도 계산

v2 진화:
  - target = v1 occ_pct
  - features: line_idx, hour, n_stations, trains_per_h, line_cap_ratio,
              is_peak_morning, is_peak_evening, is_hub (k=3 클러스터),
              archetype_office (홀수 호선), 노선 타입
  - GradientBoostingRegressor (n_estimators=200, max_depth=4)
  - 5-fold CV → R² + MAE 검증
  - 특징 중요도 (어떤 변수가 점유율 변동을 가장 잘 설명?)
  - 잔차 산점도 (model 의 cap 도달도 + 시간 양봉 만으로 설명되나?)

산출:
  outputs/carload_v2_report.json
  outputs/carload_v2_feature_importance.png
  outputs/carload_v2_residuals.png
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
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


# 호선별 메타 (eda_line_carload + policy_roi_v3 종합)
LINE_META = {
    "1호선": {"cars": 10, "cap": 160, "headway": 4.0, "cap_ratio": 0.55, "hub": 0, "type": "office"},
    "2호선": {"cars": 10, "cap": 160, "headway": 3.0, "cap_ratio": 1.10, "hub": 1, "type": "hub"},
    "3호선": {"cars": 10, "cap": 160, "headway": 4.5, "cap_ratio": 0.85, "hub": 0, "type": "residen"},
    "4호선": {"cars": 10, "cap": 160, "headway": 4.0, "cap_ratio": 0.95, "hub": 0, "type": "hub"},
    "5호선": {"cars": 8,  "cap": 140, "headway": 5.0, "cap_ratio": 0.90, "hub": 0, "type": "residen"},
    "6호선": {"cars": 8,  "cap": 140, "headway": 6.0, "cap_ratio": 0.70, "hub": 0, "type": "leisure"},
    "7호선": {"cars": 8,  "cap": 140, "headway": 5.5, "cap_ratio": 0.95, "hub": 0, "type": "hub"},
    "8호선": {"cars": 6,  "cap": 130, "headway": 7.0, "cap_ratio": 0.75, "hub": 0, "type": "residen"},
    "9호선": {"cars": 6,  "cap": 130, "headway": 6.0, "cap_ratio": 1.10, "hub": 1, "type": "office"},
}
TYPES = ["office", "residen", "hub", "leisure"]


def synth_target(line: str, h: int) -> float:
    """v1 결과 재현 — line × hour 점유율 추정.

    실 parquet 로드 없이도 모델 검증 가능 (스키마 + cap 도달도 가설)
    """
    m = LINE_META[line]
    cap = m["cap_ratio"]
    # 시간대 demand
    am = 0.65 * np.exp(-((h - 8) ** 2) / 4.0)
    pm = 0.70 * np.exp(-((h - 18) ** 2) / 5.0)
    base = 0.20 * np.exp(-((h - 13) ** 2) / 18.0)
    night = 0.04 if h < 5 or h > 23 else 0
    raw = am + pm + base + night
    # cap 도달도 결합 — 만석 호선은 거의 평탄 (cap 효과)
    occ = raw * (0.6 + cap * 0.8)  # cap 0.55 → 1.04, cap 1.10 → 1.48
    occ = min(1.5, max(0.05, occ))
    return occ


def build_dataset():
    """호선 × 시간(0-23) × 변동 노이즈 = 9 × 24 × 5 = 1080 샘플."""
    rows = []
    rng = np.random.default_rng(42)
    for line, meta in LINE_META.items():
        for h in range(24):
            base_y = synth_target(line, h)
            # 5번 노이즈 샘플 (역마다 약간씩 다름 모방)
            for _ in range(5):
                y = base_y + rng.normal(0, 0.04)
                rows.append({
                    "line": line,
                    "hour": h,
                    "cars": meta["cars"],
                    "cap": meta["cap"],
                    "headway": meta["headway"],
                    "cap_ratio": meta["cap_ratio"],
                    "is_hub": meta["hub"],
                    "type_office": int(meta["type"] == "office"),
                    "type_residen": int(meta["type"] == "residen"),
                    "type_hub": int(meta["type"] == "hub"),
                    "type_leisure": int(meta["type"] == "leisure"),
                    "is_peak_am": int(h in [7, 8, 9]),
                    "is_peak_pm": int(h in [17, 18, 19]),
                    "trains_per_h": 60.0 / meta["headway"],
                    "occ_pct": y * 100,
                })
    return rows


def main():
    rows = build_dataset()
    print("=" * 70)
    print("MetroEyes EDA v2 - 호선 × 시간 점유 추정 GBR 회귀 + 특징 중요도")
    print("=" * 70)
    print(f"\n[dataset] {len(rows)}행 × {len(rows[0])-2}특징 (target=occ_pct)")

    feat_cols = [k for k in rows[0].keys() if k not in ("line", "occ_pct")]
    X = np.array([[r[c] for c in feat_cols] for r in rows], dtype=float)
    y = np.array([r["occ_pct"] for r in rows], dtype=float)

    try:
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.model_selection import cross_val_score, KFold
        from sklearn.metrics import mean_absolute_error
    except ImportError:
        print("[warn] sklearn 미설치 — 회귀 검증 생략, 특징 분포만 출력")
        return

    model = GradientBoostingRegressor(n_estimators=200, max_depth=4, random_state=42)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    # 5-fold CV R²
    cv_r2 = cross_val_score(model, X, y, cv=kf, scoring="r2")
    cv_mae = -cross_val_score(model, X, y, cv=kf, scoring="neg_mean_absolute_error")
    print(f"\n[5-fold CV]")
    print(f"  R²  : {cv_r2.mean():.3f} ± {cv_r2.std():.3f}  (folds: {[f'{x:.3f}' for x in cv_r2]})")
    print(f"  MAE : {cv_mae.mean():.2f}%p ± {cv_mae.std():.2f}")

    # 전체 학습 → 특징 중요도
    model.fit(X, y)
    imp = model.feature_importances_
    order = np.argsort(imp)[::-1]
    print(f"\n[특징 중요도] (GBR feature_importances_)")
    print(f"  {'rank':<6}{'feature':<18}{'importance':>12}")
    print("  " + "-" * 38)
    for rank, idx in enumerate(order[:10], 1):
        bar = "█" * int(imp[idx] * 40)
        print(f"  {rank:<6}{feat_cols[idx]:<18}{imp[idx]:>10.3f}  {bar}")

    # 잔차
    yhat = model.predict(X)
    resid = y - yhat
    mae = float(mean_absolute_error(y, yhat))
    print(f"\n[잔차] MAE(전체) {mae:.2f}%p · 표준편차 {resid.std():.2f}")

    # 가장 큰 잔차 5개 (모델이 못 잡은 패턴)
    big = np.argsort(np.abs(resid))[-5:][::-1]
    print(f"\n  큰 잔차 top 5 — 모델이 놓친 케이스:")
    for i in big:
        print(f"    {rows[i]['line']:<8} {rows[i]['hour']:>2}시 — 실측 {y[i]:.0f}% · 예측 {yhat[i]:.0f}% (Δ {resid[i]:+.1f})")

    # JSON 저장
    summary = {
        "n_samples": len(rows),
        "n_features": len(feat_cols),
        "features": feat_cols,
        "cv_r2_mean": float(cv_r2.mean()),
        "cv_r2_std": float(cv_r2.std()),
        "cv_mae_mean": float(cv_mae.mean()),
        "cv_mae_std": float(cv_mae.std()),
        "feature_importance_top5": [
            {"feature": feat_cols[i], "importance": float(imp[i])}
            for i in order[:5]
        ],
        "limitation": "synth target — 실 parquet HR_*_GET_ON_NOPE 직접 회귀 시 더 풍부 (다음 단계)",
    }
    with (OUT / "carload_v2_report.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n  >> {OUT / 'carload_v2_report.json'}")

    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for name in ("Malgun Gothic", "NanumGothic"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break
        # 특징 중요도 막대
        fig, ax = plt.subplots(figsize=(9, 5))
        names = [feat_cols[i] for i in order[:10]]
        vals = [imp[i] for i in order[:10]]
        ax.barh(range(len(vals)), vals, color="#7dd3d3")
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels(names)
        ax.invert_yaxis()
        ax.set_xlabel("Importance")
        ax.set_title(f"GBR 특징 중요도 — 호선×시간 점유율 (CV R²={cv_r2.mean():.3f})")
        plt.tight_layout()
        png1 = OUT / "carload_v2_feature_importance.png"
        plt.savefig(png1, dpi=120)
        plt.close()
        print(f"  >> {png1}")
        # 잔차 산점
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(yhat, resid, alpha=0.4, s=18, c="#10b981")
        ax.axhline(0, color="white", lw=1, alpha=0.4)
        ax.set_xlabel("예측 점유율 (%)")
        ax.set_ylabel("잔차 (실측 - 예측)")
        ax.set_title(f"GBR 잔차 — MAE {mae:.2f}%p (시간×호선 양봉 모델)")
        plt.tight_layout()
        png2 = OUT / "carload_v2_residuals.png"
        plt.savefig(png2, dpi=120)
        plt.close()
        print(f"  >> {png2}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
