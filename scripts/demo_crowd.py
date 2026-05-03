"""군중 영상으로 tesla_bev 파이프라인 객관 검증.

사용:
  python scripts/demo_crowd.py [video_path]
기본: test/vtest.avi (OpenCV 표준 보행자 벤치마크).

산출:
  outputs/crowd_demo/snap_NNNN.png  대표 프레임 5장
  outputs/crowd_demo/result.mp4     원본+BEV 사이드바이사이드
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.cv.tesla_bev import Pipeline


def draw_overlay_on_frame(frame: np.ndarray, tracks: list) -> None:
    H, W = frame.shape[:2]
    for t in tracks:
        cx = int(t["bev_x"] * W)
        cy = int(t["bev_y"] * H)
        cv2.circle(frame, (cx, cy), 9, (190, 230, 230), 2)
        cv2.circle(frame, (cx, cy), 3, (210, 240, 240), -1)
        cv2.putText(frame, f"#{t['id']}", (cx + 11, cy - 9),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (210, 240, 240), 1, cv2.LINE_AA)


def draw_bev_panel(out_h: int, panel_w: int, tracks: list) -> np.ndarray:
    panel = np.full((out_h, panel_w, 3), (10, 14, 22), dtype=np.uint8)
    # 헤더
    cv2.putText(panel, "BEV (top-down)", (12, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 220, 230), 1, cv2.LINE_AA)
    cv2.rectangle(panel, (10, 32), (panel_w - 10, out_h - 14), (35, 60, 80), 1)
    # 격자
    inner_w = panel_w - 20
    inner_h = out_h - 32 - 14
    for i in range(1, 10):
        x = 10 + int(inner_w * i / 10)
        cv2.line(panel, (x, 32), (x, out_h - 14), (28, 45, 60), 1)
    for i in range(1, 8):
        y = 32 + int(inner_h * i / 8)
        cv2.line(panel, (10, y), (panel_w - 10, y), (28, 45, 60), 1)
    # 사람 마커
    for t in tracks:
        bx = 10 + int(t["bev_x"] * inner_w)
        by = 32 + int(t["bev_y"] * inner_h)
        # 글로우
        cv2.circle(panel, (bx, by), 18, (60, 130, 130), 1)
        cv2.circle(panel, (bx, by), 12, (90, 180, 180), 2)
        cv2.circle(panel, (bx, by), 5, (180, 230, 230), -1)
        cv2.putText(panel, f"#{t['id']}", (bx + 9, by - 9),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 220, 230), 1, cv2.LINE_AA)
    return panel


def main() -> None:
    video_path = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "test" / "vtest.avi")
    out_dir = ROOT / "outputs" / "crowd_demo"
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[X] 비디오 열기 실패: {video_path}")
        return
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[i] {video_path}  {W}x{H}  fps={fps:.1f}  frames={total}")

    pipe = Pipeline()

    panel_w = 280
    out_w = W + panel_w
    out_h = H
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_dir / "result.mp4"), fourcc, fps, (out_w, out_h))

    snap_frames = set([20, 80, 150, 250, 380])
    track_counts: list[int] = []
    frame_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        # 파이프라인은 JPEG 입력이라 인코딩→호출
        ok_jpg, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
        if not ok_jpg:
            continue
        payload = pipe.process_jpeg(jpg.tobytes())

        canvas = np.zeros((out_h, out_w, 3), dtype=np.uint8)
        canvas[:H, :W] = frame.copy()

        tracks = payload["tracks"] if payload else []
        track_counts.append(len(tracks))
        draw_overlay_on_frame(canvas[:H, :W], tracks)
        canvas[:H, W:] = draw_bev_panel(out_h, panel_w, tracks)

        cv2.putText(canvas, f"frame {frame_idx:>4} | tracks {len(tracks):>2}",
                    (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 230, 240), 1, cv2.LINE_AA)

        writer.write(canvas)
        if frame_idx in snap_frames:
            cv2.imwrite(str(out_dir / f"snap_{frame_idx:04d}.png"), canvas)
            print(f"  [snap] frame {frame_idx} → tracks={len(tracks)}")
        frame_idx += 1

    cap.release()
    writer.release()

    # 요약
    if track_counts:
        avg = sum(track_counts) / len(track_counts)
        mx = max(track_counts)
        mn_nonzero = min((c for c in track_counts if c > 0), default=0)
        print(f"\n[요약] 총 {frame_idx} 프레임")
        print(f"  평균 트랙 수: {avg:.1f}")
        print(f"  최대 트랙 수: {mx}")
        print(f"  최소(>=1)   : {mn_nonzero}")
        # 분포
        bins = [0, 1, 3, 5, 8, 12, 100]
        counts = [0] * (len(bins) - 1)
        for c in track_counts:
            for i in range(len(bins) - 1):
                if bins[i] <= c < bins[i + 1]:
                    counts[i] += 1
                    break
        print("  분포:")
        for i, c in enumerate(counts):
            label = f"{bins[i]}~{bins[i + 1] - 1}"
            print(f"    {label:>6}: {'#' * (c * 40 // max(1, frame_idx)):<40} {c}")
    print(f"[v] 저장: {out_dir}/")


if __name__ == "__main__":
    main()
