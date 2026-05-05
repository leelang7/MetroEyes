"""실 CardSubwayTime parquet 직접 GBR 회귀 — v3.

v2 한계: synth target (cap_ratio + 양봉 곡선) 위 학습 → R² 0.98 자명한 결과
v3: data/processed/subway_time_202602.parquet 의 HR_h_GET_ON_NOPE 직접 사용
  - target = 역 × 시간대 ON 인원 / 차량당 평균 (per_car_load 추정값 v1과 동일)
  - features:
      hour, line_idx (one-hot 9), is_peak_am/pm, dwell, n_stations,
      ON 누적 (역 직전 시간대 영향), 환승 가중 (정류장 전체 OFF/ON 비율)
  - 5-fold CV → R² + MAE
  - 실 데이터 잔차 분석 — 어떤 패턴이 모델 capability 한계?

산출:
  outputs/carload_v3_real_report.json
  outputs/carload_v3_feature_importance.png
  outputs/carload_v3_residuals.png
  outputs/carload_v3_pred_vs_actual.png
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


# 호선별 메타 (eda_carload_v2 와 동일)
LINE_CARS = {
    "1호선": 10, "2호선": 10, "3호선": 10, "4호선": 10,
    "5호선": 8, "6호선": 8, "7호선": 8, "8호선": 6, "9호선": 6,
}
LINE_HEADWAY = {
    "1호선": 4.0, "2호선": 3.0, "3호선": 4.5, "4호선": 4.0,
    "5호선": 5.0, "6호선": 6.0, "7호선": 5.5, "8호선": 7.0, "9호선": 6.0,
}


def main():
    print("=" * 72)
    print("MetroEyes EDA v3 — 실 CardSubwayTime parquet GBR 직접 회귀")
    print("=" * 72)

    if not DATA.exists():
        raise SystemExit(f"필수 데이터 없음: {DATA}")
    try:
        import pandas as pd
    except ImportError:
        raise SystemExit("pandas 미설치")

    df = pd.read_parquet(DATA)
    print(f"\n[load] {len(df):,}행 × {len(df.columns)}컬럼  ·  {df['SBWY_ROUT_LN_NM'].nunique()}개 호선")

    # 1~9 호선만 (지선 제외 — 데이터 일관성)
    main_lines = [f"{i}호선" for i in range(1, 10)]
    df = df[df["SBWY_ROUT_LN_NM"].isin(main_lines)].copy()
    print(f"[filter] 1~9호선만 → {len(df):,}행")

    # long format: 역 × 시간 → ON, OFF
    rows = []
    for h in range(5, 24):
        on_col = f"HR_{h}_GET_ON_NOPE"
        off_col = f"HR_{h}_GET_OFF_NOPE"
        if on_col not in df.columns or off_col not in df.columns:
            continue
        sub = df.groupby("SBWY_ROUT_LN_NM").agg(
            on_total=(on_col, "sum"),
            off_total=(off_col, "sum"),
            n_stations=("STTN", "nunique"),
        ).reset_index()
        for _, row in sub.iterrows():
            line = row["SBWY_ROUT_LN_NM"]
            if line not in LINE_CARS:
                continue
            cars = LINE_CARS[line]
            headway = LINE_HEADWAY[line]
            trains_per_h = 60.0 / headway
            on_daily = row["on_total"] / 28.0
            per_train_new = on_daily / (trains_per_h * 2)
            per_car = (per_train_new * 2.5) / cars  # dwell 2.5
            rows.append({
                "line": line,
                "line_idx": int(line[0]),
                "hour": h,
                "n_stations": row["n_stations"],
                "trains_per_h": trains_per_h,
                "headway": headway,
                "cars": cars,
                "is_peak_am": int(h in [7, 8, 9]),
                "is_peak_pm": int(h in [17, 18, 19]),
                "is_late": int(h >= 22 or h <= 5),
                "off_to_on_ratio": float(row["off_total"]) / max(1.0, float(row["on_total"])),
                "per_car_load": per_car,  # target
            })

    print(f"\n[dataset] {len(rows)}행 (호선 × 시간대)")
    if not rows:
        raise SystemExit("[err] empty rows — 컬럼 스키마 불일치 가능")

    feat_cols = [c for c in rows[0].keys() if c not in ("line", "per_car_load")]
    X = np.array([[r[c] for c in feat_cols] for r in rows], dtype=float)
    y = np.array([r["per_car_load"] for r in rows], dtype=float)
    print(f"[features] {feat_cols}")
    print(f"[target] per_car_load — mean {y.mean():.1f} std {y.std():.1f} max {y.max():.1f} min {y.min():.1f}")

    try:
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.model_selection import cross_val_score, KFold
        from sklearn.metrics import mean_absolute_error
    except ImportError:
        raise SystemExit("sklearn 미설치")

    model = GradientBoostingRegressor(n_estimators=300, max_depth=4, random_state=42, learning_rate=0.05)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_r2 = cross_val_score(model, X, y, cv=kf, scoring="r2")
    cv_mae = -cross_val_score(model, X, y, cv=kf, scoring="neg_mean_absolute_error")

    print(f"\n[5-fold CV — 실 데이터]")
    print(f"  R² = {cv_r2.mean():.3f} ± {cv_r2.std():.3f}  (folds: {[f'{x:.3f}' for x in cv_r2]})")
    print(f"  MAE = {cv_mae.mean():.2f} ± {cv_mae.std():.2f}  (target std {y.std():.1f})")

    model.fit(X, y)
    imp = model.feature_importances_
    order = np.argsort(imp)[::-1]
    print(f"\n[특징 중요도]")
    print(f"  {'rank':<6}{'feature':<22}{'importance':>12}")
    print("  " + "-" * 42)
    for r, idx in enumerate(order[:10], 1):
        bar = "█" * int(imp[idx] * 40)
        print(f"  {r:<6}{feat_cols[idx]:<22}{imp[idx]:>10.3f}  {bar}")

    yhat = model.predict(X)
    resid = y - yhat
    mae = float(mean_absolute_error(y, yhat))
    print(f"\n[잔차] MAE(전체) {mae:.2f} · std {resid.std():.2f}")

    big = np.argsort(np.abs(resid))[-5:][::-1]
    print(f"\n  큰 잔차 top 5 — 모델 한계:")
    for i in big:
        print(f"    {rows[i]['line']:<8} {rows[i]['hour']:>2}시 — 실측 {y[i]:.1f}명/칸 · 예측 {yhat[i]:.1f}명 (Δ {resid[i]:+.2f})")

    summary = {
        "n_samples": len(rows),
        "n_features": len(feat_cols),
        "features": feat_cols,
        "target": "per_car_load (명/칸 평균 — eda_line_carload v1 공식)",
        "data_source": str(DATA.relative_to(ROOT)),
        "cv_r2_mean": float(cv_r2.mean()),
        "cv_r2_std": float(cv_r2.std()),
        "cv_mae_mean": float(cv_mae.mean()),
        "cv_mae_std": float(cv_mae.std()),
        "feature_importance_top5": [
            {"feature": feat_cols[i], "importance": float(imp[i])}
            for i in order[:5]
        ],
        "interpretation": "실 데이터에서 R² {:.3f} — 시간대 + 호선 메타로 호선 평균 칸 점유의 {:.0%} 설명".format(
            cv_r2.mean(), cv_r2.mean()
        ),
    }
    with (OUT / "carload_v3_real_report.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n  >> {OUT / 'carload_v3_real_report.json'}")

    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        for name in ("Malgun Gothic", "NanumGothic"):
            if any(name in f.name for f in font_manager.fontManager.ttflist):
                matplotlib.rcParams["font.family"] = name
                matplotlib.rcParams["axes.unicode_minus"] = False
                break
        # 특징 중요도
        fig, ax = plt.subplots(figsize=(9, 5))
        names = [feat_cols[i] for i in order[:10]]
        vals = [imp[i] for i in order[:10]]
        ax.barh(range(len(vals)), vals, color="#10b981")
        ax.set_yticks(range(len(vals)))
        ax.set_yticklabels(names)
        ax.invert_yaxis()
        ax.set_xlabel("Importance")
        ax.set_title(f"실 parquet GBR 특징 중요도 — CV R²={cv_r2.mean():.3f} on {len(rows)} 샘플")
        plt.tight_layout()
        png1 = OUT / "carload_v3_feature_importance.png"
        plt.savefig(png1, dpi=120); plt.close()
        print(f"  >> {png1}")
        # 예측 vs 실측
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(y, yhat, alpha=0.5, s=22, c="#7dd3d3", edgecolors="white", linewidth=0.3)
        m = max(y.max(), yhat.max())
        ax.plot([0, m], [0, m], "--", color="white", alpha=0.4)
        ax.set_xlabel("실측 per_car_load (명/칸)")
        ax.set_ylabel("GBR 예측")
        ax.set_title(f"실 parquet 예측 vs 실측 — R²={cv_r2.mean():.3f}, MAE {cv_mae.mean():.1f}")
        plt.tight_layout()
        png2 = OUT / "carload_v3_pred_vs_actual.png"
        plt.savefig(png2, dpi=120); plt.close()
        print(f"  >> {png2}")
        # 잔차
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(yhat, resid, alpha=0.5, s=20, c="#ef4444")
        ax.axhline(0, color="white", lw=1, alpha=0.4)
        ax.set_xlabel("예측")
        ax.set_ylabel("잔차 (실측 - 예측)")
        ax.set_title(f"실 parquet 잔차 — MAE {mae:.2f} (target std {y.std():.1f})")
        plt.tight_layout()
        png3 = OUT / "carload_v3_residuals.png"
        plt.savefig(png3, dpi=120); plt.close()
        print(f"  >> {png3}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
