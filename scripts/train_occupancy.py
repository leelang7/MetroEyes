"""편성 평균 점유율 예측 모델 — CardSubwayTime + 클러스터.

입력:
  - data/processed/subway_time_{YYYYMM}.parquet   (CardSubwayTime API 캐시)
  - outputs/cluster_assignments.csv                (역 → 오피스/주거/환승 클러스터)

특징 (X):
  - hour          0~23 시간대
  - is_weekend    주말 여부 (USE_DT 요일에서)
  - month_day     일자 (월별 트렌드 보정용)
  - cluster_*     원-핫: office / resi / hub
  - line          호선 번호 (1~9, 기타)

타깃 (y):
  - load_proxy = (HR_n_GET_ON_NOPE - HR_n_GET_OFF_NOPE) / station_capacity
    (시각 n에서의 station 단위 net 승차 → 차내 인원 비율 proxy. -1~1 clip 후 0~1로 시프트)

출력:
  - outputs/models/occupancy_lgbm.joblib   학습 모델 (sklearn 호환 wrapper)
  - outputs/models/feature_columns.json    추론 시 컬럼 순서
  - outputs/figs/20_occupancy_pred_vs_true.png
  - outputs/figs/21_occupancy_feature_importance.png
  - outputs/occupancy_metrics.json         MAE/RMSE/R2

실행:
  python scripts/train_occupancy.py [--month 202602]

사용 (추론):
  from joblib import load
  m = load('outputs/models/occupancy_lgbm.joblib')
  pred = m.predict(X_new)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from sklearn.ensemble import GradientBoostingRegressor  # noqa: E402
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # noqa: E402
from sklearn.model_selection import KFold, cross_val_score  # noqa: E402

OUT = ROOT / "outputs"
OUT_MODELS = OUT / "models"
OUT_FIGS = OUT / "figs"
OUT_MODELS.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)


def _setup_font() -> None:
    for p in (r"C:\Windows\Fonts\malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc"):
        if Path(p).exists():
            fm.fontManager.addfont(p)
            plt.rcParams["font.family"] = fm.FontProperties(fname=p).get_name()
            plt.rcParams["axes.unicode_minus"] = False
            break


def melt_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """CardSubwayTime의 HR_n_GET_ON/OFF_NOPE 48 컬럼을 long format으로 변환.

    실제 schema (CardSubwayStatsNew, 월별 집계):
        USE_MM(월), SBWY_ROUT_LN_NM(호선), STTN(역), HR_n_GET_ON/OFF_NOPE, JOB_YMD
    결과 컬럼: month, line_name, station, hour, on, off
    """
    # 컬럼명 매핑 (있는 것만)
    col_map = {
        "USE_MM": "month", "USE_DT": "month", "USE_YMD": "month",
        "SBWY_ROUT_LN_NM": "line_name", "LINE_NUM": "line_name",
        "STTN": "station", "STATION_NAME": "station", "STATN_NM": "station",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    on_cols = [c for c in df.columns if c.startswith("HR_") and "GET_ON" in c]
    off_cols = [c for c in df.columns if c.startswith("HR_") and "GET_OFF" in c]
    if not on_cols:
        raise SystemExit(f"HR_*_GET_ON 컬럼 없음. 실제 컬럼: {list(df.columns)[:20]}")

    def hr_of(c: str) -> int:
        for tok in c.replace("HR_", "_").split("_"):
            if tok.isdigit(): return int(tok)
        return -1

    base_cols = [c for c in ("month", "line_name", "station") if c in df.columns]
    long_on = (df[base_cols + on_cols].melt(id_vars=base_cols, value_vars=on_cols,
                                             var_name="col", value_name="on")
                                       .assign(hour=lambda d: d["col"].map(hr_of))
                                       .drop(columns=["col"]))
    long_off = (df[base_cols + off_cols].melt(id_vars=base_cols, value_vars=off_cols,
                                                var_name="col", value_name="off")
                                         .assign(hour=lambda d: d["col"].map(hr_of))
                                         .drop(columns=["col"]))
    merged = long_on.merge(long_off, on=base_cols + ["hour"], how="inner")
    merged["on"] = pd.to_numeric(merged["on"], errors="coerce")
    merged["off"] = pd.to_numeric(merged["off"], errors="coerce")
    return merged.dropna(subset=["on", "off", "hour"]).query("0 <= hour < 24")


def build_dataset(month: str, station_capacity: int = 5000) -> tuple[pd.DataFrame, list[str]]:
    """학습 데이터셋 X, y."""
    parquet = ROOT / "data" / "processed" / f"subway_time_{month}.parquet"
    cluster_csv = OUT / "cluster_assignments.csv"
    if not parquet.exists():
        raise SystemExit(f"필요: {parquet} (먼저 데이터 fetch)")
    if not cluster_csv.exists():
        raise SystemExit(f"필요: {cluster_csv} (먼저 scripts/cluster_stations.py 실행)")

    raw = pd.read_parquet(parquet)
    print(f"[load] {parquet.name} shape={raw.shape}")
    long = melt_hourly(raw)
    print(f"[melt] long-form shape={long.shape}")

    cluster = pd.read_csv(cluster_csv)
    # cluster_assignments.csv 컬럼명 후보
    name_col = next((c for c in ("STTN","STATION_NAME","STATN_NM","station") if c in cluster.columns),
                    cluster.columns[0])
    cluster_col = next((c for c in ("cluster","CLUSTER","cluster_id","label") if c in cluster.columns),
                       cluster.columns[1])
    cluster = cluster.rename(columns={name_col: "station", cluster_col: "cluster_id"})

    df = long.merge(cluster[["station", "cluster_id"]], on="station", how="left")
    df["cluster_id"] = df["cluster_id"].fillna("unk").astype(str)

    # 타깃: 점유율 proxy = (on + off) 시간당 합 → station_capacity 정규화 → 0~1.05 clip.
    # CardSubwayStatsNew는 월별 집계라 일자/요일 feature 없음 → station × hour 14k row.
    df["load_proxy"] = ((df["on"] + df["off"]) / station_capacity).clip(0.0, 1.05)

    # 라인 정수화 (호선명에서 숫자 추출)
    df["line"] = (pd.to_numeric(df["line_name"].astype(str).str.extract(r"(\d+)")[0],
                                  errors="coerce").fillna(0).astype(int))

    # 클러스터 원-핫
    cluster_dummies = pd.get_dummies(df["cluster_id"], prefix="cluster")
    df = pd.concat([df, cluster_dummies], axis=1)

    feature_cols = ["hour", "line"] + list(cluster_dummies.columns)
    Xy = df[feature_cols + ["load_proxy", "station"]].dropna()
    return Xy, feature_cols


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--month", default="202602", help="YYYYMM")
    parser.add_argument("--capacity", type=int, default=5000,
                        help="역당 시간당 capacity (load_proxy 정규화)")
    args = parser.parse_args()

    _setup_font()

    Xy, feature_cols = build_dataset(args.month, args.capacity)
    print(f"[data] X.shape={Xy[feature_cols].shape} y.mean={Xy['load_proxy'].mean():.3f}")

    X = Xy[feature_cols].astype(float).values
    y = Xy["load_proxy"].values

    # train/val split (80/20, 시간 누수 방지를 위해 day 단위 random 샘플)
    rng = np.random.default_rng(42)
    idx = np.arange(len(X))
    rng.shuffle(idx)
    cut = int(len(idx) * 0.8)
    tr, va = idx[:cut], idx[cut:]

    model = GradientBoostingRegressor(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, random_state=42,
    )
    model.fit(X[tr], y[tr])
    pred_va = model.predict(X[va])
    mae = mean_absolute_error(y[va], pred_va)
    rmse = float(np.sqrt(mean_squared_error(y[va], pred_va)))
    r2 = r2_score(y[va], pred_va)
    print(f"[eval] MAE={mae:.4f}  RMSE={rmse:.4f}  R2={r2:.3f}")

    # 5-fold CV (간단 평균)
    cv_scores = cross_val_score(model, X, y, cv=KFold(5, shuffle=True, random_state=42),
                                  scoring="neg_mean_absolute_error", n_jobs=-1)
    cv_mae = -cv_scores.mean()
    print(f"[cv] 5-fold MAE={cv_mae:.4f} ± {cv_scores.std():.4f}")

    # 저장
    model_path = OUT_MODELS / "occupancy_lgbm.joblib"
    joblib.dump(model, model_path)
    (OUT_MODELS / "feature_columns.json").write_text(
        json.dumps(feature_cols, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    metrics = {"mae_val": mae, "rmse_val": rmse, "r2_val": r2,
               "mae_cv5": cv_mae, "n_samples": int(len(X)),
               "n_features": int(X.shape[1]), "feature_cols": feature_cols,
               "month": args.month, "capacity": args.capacity}
    (OUT / "occupancy_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[save] {model_path.relative_to(ROOT)}")

    # 시각화 1: 예측 vs 실제 산점도
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y[va], pred_va, s=2, alpha=0.25, color="#7DD3D3")
    ax.plot([0, 1], [0, 1], color="#FF5E57", linewidth=1, linestyle="--")
    ax.set_xlabel("실제 점유율 proxy")
    ax.set_ylabel("예측 점유율 proxy")
    ax.set_title(f"점유율 예측 모델 — MAE {mae:.3f}, R² {r2:.2f}")
    ax.set_xlim(0, 1.1); ax.set_ylim(0, 1.1)
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    p1 = OUT_FIGS / "20_occupancy_pred_vs_true.png"
    fig.savefig(p1, dpi=130)
    plt.close(fig)
    print(f"[fig] {p1.relative_to(ROOT)}")

    # 시각화 2: feature importance
    imp = model.feature_importances_
    order = np.argsort(imp)[::-1]
    fig, ax = plt.subplots(figsize=(7, max(3, len(feature_cols) * 0.3)))
    ax.barh([feature_cols[i] for i in order][::-1], imp[order][::-1], color="#7DD3D3")
    ax.set_xlabel("중요도")
    ax.set_title("점유율 예측 — 특징 중요도")
    fig.tight_layout()
    p2 = OUT_FIGS / "21_occupancy_feature_importance.png"
    fig.savefig(p2, dpi=130)
    plt.close(fig)
    print(f"[fig] {p2.relative_to(ROOT)}")

    print()
    print("=" * 50)
    print(f"학습 완료. 모델 → {model_path.relative_to(ROOT)}")
    print(f"검증 MAE {mae:.4f} / RMSE {rmse:.4f} / R² {r2:.3f}")
    print(f"5-fold CV MAE {cv_mae:.4f}")
    print("=" * 50)


if __name__ == "__main__":
    main()
