"""src/cv/homography.py 단위 테스트 — save/project 순수 함수 (YOLO 불필요) (cycle 503).

호모그래피 파이프라인:
- save_homography: JSON 파일 저장 + 필수 필드 검증
- project_points: (N,2) 이미지 픽셀 → BEV 좌표 변환
- project_points 에지 케이스: 빈 배열, 단일 점, identity-like H
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

# cv2 없을 경우 스킵 (CI 비 OpenCV 환경)
cv2 = pytest.importorskip("cv2")


def _make_H() -> np.ndarray:
    """단위 테스트용 실제 호모그래피 — 4개 비공선 점으로 계산."""
    src = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.float32)
    dst = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
    H, _ = cv2.findHomography(src, dst, method=0)
    return H


# ────────────────── project_points ──────────────────

def test_project_points_empty() -> None:
    """빈 배열 → 빈 배열 반환 (shape 유지)."""
    from src.cv.homography import project_points
    H = _make_H()
    pts = np.empty((0, 2), dtype=np.float32)
    out = project_points(H, pts)
    assert out.shape == pts.shape


def test_project_points_single() -> None:
    """단일 점 (1,2) → 변환 정상."""
    from src.cv.homography import project_points
    H = _make_H()
    pts = np.array([[50, 50]], dtype=np.float32)
    out = project_points(H, pts)
    assert out.shape == (1, 2)


def test_project_points_corner_origin() -> None:
    """코너 (0,0) → BEV 원점 근처 (오차 1e-3 이내)."""
    from src.cv.homography import project_points
    H = _make_H()
    pts = np.array([[0.0, 0.0]], dtype=np.float32)
    out = project_points(H, pts)
    assert abs(out[0, 0]) < 1e-3 and abs(out[0, 1]) < 1e-3


def test_project_points_corner_full() -> None:
    """코너 (100,100) → BEV (1,1) 근처."""
    from src.cv.homography import project_points
    H = _make_H()
    pts = np.array([[100.0, 100.0]], dtype=np.float32)
    out = project_points(H, pts)
    assert abs(out[0, 0] - 1.0) < 1e-3 and abs(out[0, 1] - 1.0) < 1e-3


def test_project_points_multiple() -> None:
    """여러 점 → 출력 shape (N,2)."""
    from src.cv.homography import project_points
    H = _make_H()
    pts = np.array([[0, 0], [50, 0], [100, 100], [0, 100]], dtype=np.float32)
    out = project_points(H, pts)
    assert out.shape == (4, 2)


# ────────────────── save_homography ──────────────────

def test_save_homography_returns_path(tmp_path, monkeypatch) -> None:
    """save_homography 반환값이 Path 객체."""
    from src.cv import homography as hm
    monkeypatch.setattr(hm, "CONFIG_DIR", tmp_path)
    from src.cv.homography import save_homography
    ret = save_homography(
        "test_cam",
        [(0, 0), (100, 0), (100, 100), (0, 100)],
        [(0, 0), (1, 0), (1, 1), (0, 1)],
        (100, 100),
    )
    assert isinstance(ret, Path)


def test_save_homography_creates_json(tmp_path, monkeypatch) -> None:
    """save_homography가 JSON 파일을 생성."""
    from src.cv import homography as hm
    monkeypatch.setattr(hm, "CONFIG_DIR", tmp_path)
    from src.cv.homography import save_homography
    save_homography(
        "cam_a",
        [(0, 0), (80, 0), (80, 60), (0, 60)],
        [(0, 0), (1, 0), (1, 1), (0, 1)],
        (80, 60),
    )
    fp = tmp_path / "homography_cam_a.json"
    assert fp.is_file()


def test_save_homography_json_fields(tmp_path, monkeypatch) -> None:
    """저장된 JSON에 cam_id/image_points/bev_points/image_size 필드 존재."""
    from src.cv import homography as hm
    monkeypatch.setattr(hm, "CONFIG_DIR", tmp_path)
    from src.cv.homography import save_homography
    save_homography(
        "cam_b",
        [(10, 20), (90, 20), (90, 80), (10, 80)],
        [(0, 0), (1, 0), (1, 1), (0, 1)],
        (100, 100),
    )
    data = json.loads((tmp_path / "homography_cam_b.json").read_text(encoding="utf-8"))
    for field in ("cam_id", "image_points", "bev_points", "image_size"):
        assert field in data, f"JSON 필드 {field} 누락"
    assert data["cam_id"] == "cam_b"


def test_save_then_load_roundtrip(tmp_path, monkeypatch) -> None:
    """save 후 load → 변환 결과 일관성."""
    from src.cv import homography as hm
    monkeypatch.setattr(hm, "CONFIG_DIR", tmp_path)
    from src.cv.homography import save_homography, load_homography, project_points

    img_pts = [(0, 0), (100, 0), (100, 100), (0, 100)]
    bev_pts = [(0, 0), (1, 0), (1, 1), (0, 1)]
    save_homography("roundtrip", img_pts, bev_pts, (100, 100))

    H, cfg = load_homography("roundtrip")
    assert cfg["cam_id"] == "roundtrip"
    pts = np.array([[0.0, 0.0]], dtype=np.float32)
    out = project_points(H, pts)
    assert abs(out[0, 0]) < 1e-2 and abs(out[0, 1]) < 1e-2


def test_load_homography_missing_file(tmp_path, monkeypatch) -> None:
    """존재하지 않는 cam_id → FileNotFoundError."""
    from src.cv import homography as hm
    monkeypatch.setattr(hm, "CONFIG_DIR", tmp_path)
    from src.cv.homography import load_homography
    with pytest.raises(FileNotFoundError):
        load_homography("nonexistent_cam")
