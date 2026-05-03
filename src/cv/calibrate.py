"""인터랙티브 4점 호모그래피 캘리브레이션 도구.

사용:
  # 웹캠으로 즉시
  python -m src.cv.calibrate --cam ceiling --source 0

  # 미리 캡처한 이미지에서
  python -m src.cv.calibrate --cam ceiling --image snap.jpg

화면에 차량(또는 바닥 직사각형) 4개 모서리를 시계 방향으로 클릭:
  좌상 → 우상 → 우하 → 좌하

저장 후 `configs/homography_<cam_id>.json` 생성.
BEV 평면은 [0,1] x [0,1] 정규화 (좌상 0,0 / 우하 1,1).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from src.cv.homography import save_homography


CORNER_HINTS = ["좌상 (0,0)", "우상 (1,0)", "우하 (1,1)", "좌하 (0,1)"]
BEV_TARGETS = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]


def grab_image(source: str, image_path: str | None) -> tuple[np.ndarray, tuple[int, int]]:
    if image_path:
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(image_path)
    else:
        cap_index = int(source) if source.isdigit() else source
        cap = cv2.VideoCapture(cap_index)
        if not cap.isOpened():
            raise RuntimeError(f"카메라/소스 열기 실패: {source}")
        # 워밍업
        for _ in range(5):
            cap.read()
        ok, img = cap.read()
        cap.release()
        if not ok:
            raise RuntimeError("프레임 캡처 실패")
    return img, (img.shape[1], img.shape[0])


def pick_points(img: np.ndarray) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    win = "Calibration — 4 corners (CW from top-left)"

    def render() -> np.ndarray:
        canvas = img.copy()
        for i, (x, y) in enumerate(points):
            cv2.circle(canvas, (int(x), int(y)), 6, (60, 220, 220), 2)
            cv2.putText(
                canvas, str(i + 1), (int(x) + 9, int(y) - 9),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (60, 220, 220), 2
            )
        if len(points) >= 2:
            for i in range(len(points) - 1):
                p1 = (int(points[i][0]), int(points[i][1]))
                p2 = (int(points[i + 1][0]), int(points[i + 1][1]))
                cv2.line(canvas, p1, p2, (60, 220, 220), 1)
        if len(points) == 4:
            p1 = (int(points[3][0]), int(points[3][1]))
            p2 = (int(points[0][0]), int(points[0][1]))
            cv2.line(canvas, p1, p2, (60, 220, 220), 1)
        hint = CORNER_HINTS[len(points)] if len(points) < 4 else "ENTER=저장 / r=초기화 / q=취소"
        cv2.putText(
            canvas, f"[{len(points)}/4] {hint}",
            (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (60, 220, 220), 2
        )
        return canvas

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
            points.append((float(x), float(y)))

    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win, on_mouse)
    while True:
        cv2.imshow(win, render())
        key = cv2.waitKey(20) & 0xFF
        if key == ord("q"):
            cv2.destroyWindow(win)
            return []
        if key == ord("r"):
            points.clear()
        if key in (13, 10) and len(points) == 4:  # Enter
            cv2.destroyWindow(win)
            return points


def main() -> None:
    parser = argparse.ArgumentParser(description="4점 호모그래피 캘리브레이션")
    parser.add_argument("--cam", required=True, help="cam_id (저장 파일명에 사용)")
    parser.add_argument("--source", default="0", help="카메라 인덱스 또는 비디오 경로")
    parser.add_argument("--image", default=None, help="정적 이미지 경로 (지정 시 source 무시)")
    args = parser.parse_args()

    img, (W, H) = grab_image(args.source, args.image)
    print(f"[i] 입력 크기: {W}x{H}. 4점 시계방향 클릭 (좌상→우상→우하→좌하).")
    image_points = pick_points(img)
    if len(image_points) != 4:
        print("[!] 취소됨")
        return
    fp = save_homography(args.cam, image_points, BEV_TARGETS, (W, H))
    print(f"[v] 저장: {fp}")


if __name__ == "__main__":
    main()
