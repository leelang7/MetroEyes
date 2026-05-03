"""역 클러스터링 — 24h 시간대 승하차 프로파일(48차원, 행 정규화)을 K-means로 군집화.

산출물:
  - outputs/figs/10_cluster_mean_profiles.png   클러스터별 평균 시간대 패턴
  - outputs/figs/11_cluster_pca_embedding.png   2D PCA 임베딩에 클러스터 색
  - outputs/cluster_assignments.csv              역 → 클러스터 매핑

실행: .venv/Scripts/python scripts/cluster_stations.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from src.data_pipeline.loaders import fetch_to_parquet

MONTH = "202602"
OUT_FIGS = ROOT / "outputs" / "figs"
OUT = ROOT / "outputs"
OUT_FIGS.mkdir(parents=True, exist_ok=True)


def _setup_font() -> None:
    for p in (r"C:\Windows\Fonts\malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc"):
        if Path(p).exists():
            fm.fontManager.addfont(p)
            plt.rcParams["font.family"] = fm.FontProperties(fname=p).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 130


_setup_font()
sns.set_style("whitegrid", {"font.family": plt.rcParams["font.family"]})

URBAN = ("호선", "우이신설", "신림", "공항철도")
HOURS = list(range(4, 24)) + [0, 1, 2, 3]  # 4시→23시→0시→3시 시간순


def load_features() -> tuple[pd.DataFrame, np.ndarray, list[str]]:
    """역 단위 48차원 프로파일 (24 승차 + 24 하차, 합=1로 정규화)."""
    df = fetch_to_parquet("CardSubwayTime", MONTH, cache_name=f"subway_time_{MONTH}",
                          page=1000, max_rows=2000)
    df = df.rename(columns={"SBWY_ROUT_LN_NM": "line", "STTN": "station"})
    df = df[df["line"].apply(lambda s: any(h in s for h in URBAN))].copy()
    # 환승역(다중 호선)은 합산 — station 단위 단일 프로파일
    on_cols = [f"HR_{h}_GET_ON_NOPE" for h in HOURS]
    off_cols = [f"HR_{h}_GET_OFF_NOPE" for h in HOURS]
    for c in on_cols + off_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    agg = df.groupby("station", as_index=False)[on_cols + off_cols].sum()
    # 노이즈 역 제외 — 월간 총합 5000 미만
    agg["total"] = agg[on_cols + off_cols].sum(axis=1)
    agg = agg[agg["total"] >= 5000].reset_index(drop=True)

    raw = agg[on_cols + off_cols].values.astype(float)
    norm = raw / raw.sum(axis=1, keepdims=True).clip(min=1)
    feat_names = [f"on_{h}" for h in HOURS] + [f"off_{h}" for h in HOURS]
    return agg, norm, feat_names


def pick_k(X: np.ndarray, ks: tuple[int, ...] = (3, 4, 5, 6, 7, 8)) -> tuple[int, dict[int, float]]:
    scores: dict[int, float] = {}
    for k in ks:
        km = KMeans(n_clusters=k, n_init=20, random_state=42).fit(X)
        scores[k] = silhouette_score(X, km.labels_, sample_size=min(2000, len(X)), random_state=42)
    best = max(scores, key=scores.get)
    return best, scores


def cluster_label(cluster_profile: np.ndarray) -> str:
    """클러스터 평균 프로파일 보고 자동으로 한글 라벨 붙이기.

    cluster_profile shape = (48,), 4시→3시 순서, 앞 24=승차, 뒤 24=하차.
    """
    on = cluster_profile[:24]
    off = cluster_profile[24:]
    hours_arr = np.array(HOURS)
    am_mask = (hours_arr >= 7) & (hours_arr <= 9)
    pm_mask = (hours_arr >= 17) & (hours_arr <= 19)
    on_am, on_pm = on[am_mask].sum(), on[pm_mask].sum()
    off_am, off_pm = off[am_mask].sum(), off[pm_mask].sum()

    # 1) 양봉이면서 승차/하차 거의 균형 → 환승 허브
    am_imbalance = abs(off_am - on_am) / max(on_am, off_am, 1e-9)
    pm_imbalance = abs(on_pm - off_pm) / max(on_pm, off_pm, 1e-9)
    if am_imbalance < 0.35 and pm_imbalance < 0.35:
        return "환승 허브 (양봉 균형)"
    # 2) 출근 하차 + 퇴근 승차 우세 → 오피스형
    if off_am > on_am and on_pm > off_pm:
        return "오피스형 (출근 하차↑·퇴근 승차↑)"
    # 3) 출근 승차 + 퇴근 하차 우세 → 주거형
    if on_am > off_am and off_pm > on_pm:
        return "주거형 (출근 승차↑·퇴근 하차↑)"
    return "기타/평탄형"


def fig10_mean_profiles(meta: pd.DataFrame, X: np.ndarray, labels: np.ndarray, k: int) -> dict[int, str]:
    """클러스터별 평균 시간대 패턴 — 승차/하차 두 줄."""
    cluster_to_label: dict[int, str] = {}
    rows = (k + 1) // 2
    fig, axes = plt.subplots(rows, 2, figsize=(13, 3.2 * rows), sharex=True, sharey=True)
    axes = axes.ravel()
    palette = sns.color_palette("Set2", k)

    for ci in range(k):
        ax = axes[ci]
        mask = labels == ci
        avg = X[mask].mean(axis=0)
        on, off = avg[:24], avg[24:]
        # 4→23→0→3 순이므로 0~3시를 끝으로 보존하고 x축 라벨링은 시각으로
        x = list(range(24))
        ax.plot(x, on, "-o", color="#2E86AB", lw=1.6, ms=3.5, label="승차")
        ax.plot(x, off, "-s", color="#E08E45", lw=1.6, ms=3.5, label="하차")
        # 대표 역 Top 3 (클러스터 내 통행량 큰 순)
        clu_meta = meta[mask].copy()
        top = clu_meta.nlargest(3, "total")["station"].tolist()
        label = cluster_label(avg)
        cluster_to_label[ci] = label
        ax.set_title(
            f"C{ci} · {label}  (n={mask.sum()})\n대표: {' / '.join(top)}",
            fontsize=10,
        )
        ax.set_xticks([0, 4, 7, 11, 15, 18, 22])
        ax.set_xticklabels([HOURS[i] for i in [0, 4, 7, 11, 15, 18, 22]])
        ax.set_facecolor(palette[ci] + (0.06,))
        ax.legend(fontsize=8, loc="upper right")
    for j in range(k, len(axes)):
        axes[j].set_visible(False)
    fig.suptitle(f"역 클러스터별 시간대 평균 프로파일 (K={k}, {MONTH}, n={len(X)}개 역)", y=1.0)
    fig.tight_layout()
    p = OUT_FIGS / "10_cluster_mean_profiles.png"
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved → {p.relative_to(ROOT)}")
    return cluster_to_label


def fig11_pca(meta: pd.DataFrame, X: np.ndarray, labels: np.ndarray, name_map: dict[int, str], k: int) -> None:
    pca = PCA(n_components=2, random_state=42)
    Z = pca.fit_transform(X)
    var = pca.explained_variance_ratio_
    fig, ax = plt.subplots(figsize=(11, 7))
    palette = sns.color_palette("Set2", k)
    for ci in range(k):
        mask = labels == ci
        ax.scatter(Z[mask, 0], Z[mask, 1], s=18, alpha=0.6, color=palette[ci],
                   label=f"C{ci} · {name_map[ci]} (n={mask.sum()})")
    # 랜드마크 라벨 — 통행량 Top 12
    landmarks = meta.nlargest(12, "total").index.tolist()
    for i in landmarks:
        ax.annotate(meta.loc[i, "station"], (Z[i, 0], Z[i, 1]),
                    fontsize=9, ha="left", va="bottom", color="#222")
    ax.set_xlabel(f"PC1 ({var[0]*100:.1f}%)")
    ax.set_ylabel(f"PC2 ({var[1]*100:.1f}%)")
    ax.set_title(f"역 시간대 프로파일 — 2D PCA 임베딩  (K={k}, {MONTH})")
    ax.legend(fontsize=9, loc="best")
    p = OUT_FIGS / "11_cluster_pca_embedding.png"
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  saved → {p.relative_to(ROOT)}")


def main() -> None:
    print("[load]")
    meta, X, _ = load_features()
    print(f"  stations={len(meta)}  feature_dim={X.shape[1]}")

    print("[choose k]")
    k, scores = pick_k(X)
    for kk, s in scores.items():
        print(f"  k={kk}: silhouette={s:.3f}")
    print(f"  → 선택: k={k}")

    km = KMeans(n_clusters=k, n_init=30, random_state=42).fit(X)
    labels = km.labels_
    meta["cluster"] = labels

    print("[render]")
    name_map = fig10_mean_profiles(meta, X, labels, k)
    fig11_pca(meta, X, labels, name_map, k)

    out_csv = OUT / "cluster_assignments.csv"
    meta[["station", "cluster", "total"]].assign(
        cluster_name=meta["cluster"].map(name_map)
    ).sort_values(["cluster", "total"], ascending=[True, False]).to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"  saved → {out_csv.relative_to(ROOT)}")

    print("\n[summary] 클러스터 정의 + 대표 역 Top 5")
    for ci in range(k):
        m = meta[meta["cluster"] == ci]
        top = m.nlargest(5, "total")["station"].tolist()
        print(f"  C{ci} · {name_map[ci]}  (n={len(m)})  →  {', '.join(top)}")


if __name__ == "__main__":
    main()
