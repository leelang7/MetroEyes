"""이미지 평면 → BEV(차량 바닥) 평면 호모그래피.

저장: configs/homography_<cam_id>.json
{
  "cam_id": "ceiling_front",
  "image_points": [[x, y], ...4],   # 픽셀
  "bev_points": [[u, v], ...4],     # [0, 1] 정규화 (차량 바닥 좌표)
  "image_size": [W, H]
}
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"


def load_homography(cam_id: str) -> tuple[np.ndarray, dict]:
    """`configs/homography_{cam_id}.json` 에서 호모그래피 행렬 로드."""
    fp = CONFIG_DIR / f"homography_{cam_id}.json"
    if not fp.exists():
        raise FileNotFoundError(
            f"{fp} 없음. `python -m src.cv.calibrate --cam {cam_id}` 로 먼저 캘리브레이션."
        )
    cfg = json.loads(fp.read_text(encoding="utf-8"))
    src = np.asarray(cfg["image_points"], dtype=np.float32)
    dst = np.asarray(cfg["bev_points"], dtype=np.float32)
    H, _ = cv2.findHomography(src, dst, method=0)
    if H is None:
        raise RuntimeError(f"{fp} 호모그래피 계산 실패 — 4점이 동일선상일 가능성")
    return H, cfg


def save_homography(
    cam_id: str,
    image_points: list[tuple[float, float]],
    bev_points: list[tuple[float, float]],
    image_size: tuple[int, int],
) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    fp = CONFIG_DIR / f"homography_{cam_id}.json"
    cfg = {
        "cam_id": cam_id,
        "image_points": [[float(x), float(y)] for x, y in image_points],
        "bev_points": [[float(u), float(v)] for u, v in bev_points],
        "image_size": [int(image_size[0]), int(image_size[1])],
    }
    fp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return fp


def project_points(H: np.ndarray, points_xy: np.ndarray) -> np.ndarray:
    """이미지 좌표 (N, 2) → BEV 좌표 (N, 2). H는 cv2.findHomography 출력."""
    if points_xy.size == 0:
        return points_xy.copy()
    pts = points_xy.reshape(-1, 1, 2).astype(np.float32)
    out = cv2.perspectiveTransform(pts, H)
    return out.reshape(-1, 2)
