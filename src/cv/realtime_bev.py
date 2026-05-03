"""실시간 카메라 → YOLO11-pose → 호모그래피 → BEV 트랙 파이프라인.

스탠드얼론 실행:
  python -m src.cv.realtime_bev --cam ceiling --source 0
  python -m src.cv.realtime_bev --cam ceiling --source samples/clip.mp4

WebSocket 서버 모드 (프론트엔드와 라이브 연동):
  python -m src.cv.realtime_bev --cam ceiling --source 0 --serve --port 8765

JSON 더미 모드 (캘리브레이션 없이 화면 절반에 매핑하여 빠르게 시연):
  python -m src.cv.realtime_bev --source 0 --no-homography
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "ultralytics 미설치. `pip install ultralytics` 또는 `pip install -r requirements.txt`"
    ) from e

from src.cv.homography import load_homography, project_points


# COCO keypoint indices (yolo11n-pose)
KP_NOSE = 0
KP_L_EYE = 1
KP_R_EYE = 2
KP_L_SHOULDER = 5
KP_R_SHOULDER = 6


@dataclass
class TrackState:
    track_id: int
    history: deque = field(default_factory=lambda: deque(maxlen=12))   # [(t, bx, by)]

    def add(self, t: float, bx: float, by: float) -> None:
        self.history.append((t, bx, by))

    def heading(self) -> float | None:
        """최근 ~0.4초간 평균 속도 벡터의 atan2."""
        if len(self.history) < 2:
            return None
        t_now = self.history[-1][0]
        recent = [h for h in self.history if t_now - h[0] < 0.5]
        if len(recent) < 2:
            return None
        dx = recent[-1][1] - recent[0][1]
        dy = recent[-1][2] - recent[0][2]
        if abs(dx) + abs(dy) < 0.002:
            return None  # 정지 — 헤딩 미정
        return float(np.arctan2(dy, dx))


class Pipeline:
    """카메라 → YOLO-pose → 호모그래피 → BEV 트랙. 매 프레임 process(frame).

    출력 schema (process가 리턴):
      {
        "ts": float,
        "fps": float,
        "frame_idx": int,
        "tracks": [{"id": int, "bev_x": float, "bev_y": float, "heading": float|None, "conf": float}],
      }
    """

    def __init__(
        self,
        cam_id: str | None,
        model_name: str = "yolo11n-pose.pt",
        use_homography: bool = True,
        device: str | None = None,
    ) -> None:
        self.model = YOLO(model_name)
        if device:
            self.model.to(device)
        self.use_homography = use_homography
        if use_homography:
            if cam_id is None:
                raise ValueError("use_homography=True 인데 cam_id 가 None")
            self.H, self.cfg = load_homography(cam_id)
        else:
            self.H = None
            self.cfg = None

        self.tracks: dict[int, TrackState] = {}
        self.frame_idx = 0
        self.fps_window: deque = deque(maxlen=30)
        self._last_t = time.time()

    def _person_anchor(self, kpts_xy: np.ndarray) -> tuple[float, float] | None:
        """YOLO-pose 키포인트(17, 2)에서 BEV 앵커(머리/어깨 중간) 픽셀 좌표 추출."""
        nose = kpts_xy[KP_NOSE]
        ls = kpts_xy[KP_L_SHOULDER]
        rs = kpts_xy[KP_R_SHOULDER]
        # 어깨 중간이 가장 안정적
        if ls[0] > 0 and rs[0] > 0:
            return float((ls[0] + rs[0]) / 2), float((ls[1] + rs[1]) / 2)
        if nose[0] > 0:
            return float(nose[0]), float(nose[1])
        return None

    def process(self, frame: np.ndarray) -> dict:
        """단일 프레임 처리, BEV 트랙 dict 리턴."""
        t = time.time()
        self.fps_window.append(t - self._last_t)
        self._last_t = t
        avg_dt = sum(self.fps_window) / max(1, len(self.fps_window))
        fps = 1.0 / max(avg_dt, 1e-3)

        # YOLO 트래킹 (persist=True가 ID 유지)
        results = self.model.track(
            frame, persist=True, verbose=False,
            classes=[0],   # person만
            conf=0.35,
        )
        out_tracks = []
        if not results:
            return {"ts": t, "fps": fps, "frame_idx": self.frame_idx, "tracks": []}

        r = results[0]
        if r.boxes is None or r.boxes.id is None or r.keypoints is None:
            self.frame_idx += 1
            return {"ts": t, "fps": fps, "frame_idx": self.frame_idx, "tracks": []}

        ids = r.boxes.id.int().cpu().tolist()
        confs = r.boxes.conf.cpu().numpy()
        kpts_all = r.keypoints.xy.cpu().numpy()  # (N, 17, 2)

        H, W = frame.shape[:2]
        anchors_img: list[tuple[float, float]] = []
        valid_indices: list[int] = []
        for i, kpts in enumerate(kpts_all):
            anchor = self._person_anchor(kpts)
            if anchor is None:
                continue
            anchors_img.append(anchor)
            valid_indices.append(i)
        if not anchors_img:
            self.frame_idx += 1
            return {"ts": t, "fps": fps, "frame_idx": self.frame_idx, "tracks": []}

        pts_img = np.array(anchors_img, dtype=np.float32)
        if self.use_homography and self.H is not None:
            bev = project_points(self.H, pts_img)
        else:
            # 캘리브레이션 없이 단순 정규화 (이미지 절반 → BEV 사각형)
            bev = np.column_stack([pts_img[:, 0] / W, pts_img[:, 1] / H])

        for j, i in enumerate(valid_indices):
            tid = int(ids[i])
            bx, by = float(bev[j][0]), float(bev[j][1])
            # BEV 범위 클램프 (0~1 밖은 차량 외부로 간주, 일단 통과시킴)
            ts = self.tracks.get(tid)
            if ts is None:
                ts = TrackState(track_id=tid)
                self.tracks[tid] = ts
            ts.add(t, bx, by)
            heading = ts.heading()
            out_tracks.append({
                "id": tid,
                "bev_x": bx,
                "bev_y": by,
                "heading": heading,
                "conf": float(confs[i]),
            })

        # 오래된 트랙 정리 (3초 미관측)
        stale = [tid for tid, s in self.tracks.items() if t - s.history[-1][0] > 3.0]
        for tid in stale:
            del self.tracks[tid]

        self.frame_idx += 1
        return {"ts": t, "fps": fps, "frame_idx": self.frame_idx, "tracks": out_tracks}


# ============== Visualizer (디버그용) ==============
def draw_debug(frame: np.ndarray, payload: dict) -> np.ndarray:
    out = frame.copy()
    H, W = frame.shape[:2]
    cv2.putText(
        out, f"FPS {payload.get('fps', 0):4.1f} | tracks {len(payload.get('tracks', []))}",
        (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (60, 220, 220), 2
    )
    # BEV 미니뷰: 우상단 200x200 박스에 트랙 점
    pad = 12
    box_w, box_h = 220, 220
    x0 = W - box_w - pad
    y0 = pad
    cv2.rectangle(out, (x0, y0), (x0 + box_w, y0 + box_h), (40, 40, 50), -1)
    cv2.rectangle(out, (x0, y0), (x0 + box_w, y0 + box_h), (80, 80, 100), 1)
    cv2.putText(out, "BEV", (x0 + 8, y0 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 200, 220), 1)
    for trk in payload.get("tracks", []):
        bx = max(0.0, min(1.0, trk["bev_x"]))
        by = max(0.0, min(1.0, trk["bev_y"]))
        px = int(x0 + 4 + bx * (box_w - 8))
        py = int(y0 + 4 + by * (box_h - 8))
        cv2.circle(out, (px, py), 5, (125, 211, 211), -1)
        cv2.putText(out, str(trk["id"]), (px + 7, py - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (220, 220, 220), 1)
    return out


# ============== Runner ==============
def open_source(source: str) -> cv2.VideoCapture:
    src = int(source) if source.isdigit() else source
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise RuntimeError(f"소스 열기 실패: {source}")
    return cap


def run_local(args) -> None:
    pipe = Pipeline(args.cam if args.cam else None,
                    model_name=args.model,
                    use_homography=not args.no_homography,
                    device=args.device)
    cap = open_source(args.source)
    win = "MetroEyes — Real Pipeline (q to quit)"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        payload = pipe.process(frame)
        debug = draw_debug(frame, payload)
        cv2.imshow(win, debug)
        if (cv2.waitKey(1) & 0xFF) == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


async def run_serve(args) -> None:
    """WebSocket 브로드캐스트. 신규 asyncio API (websockets >=15)."""
    from websockets.asyncio.server import serve

    pipe = Pipeline(args.cam if args.cam else None,
                    model_name=args.model,
                    use_homography=not args.no_homography,
                    device=args.device)

    cap = open_source(args.source)
    clients: set = set()
    preview_win = "Camera Feed (q to close)" if args.preview else None
    if preview_win:
        cv2.namedWindow(preview_win, cv2.WINDOW_NORMAL)

    async def producer() -> None:
        loop = asyncio.get_running_loop()
        last_print = 0.0
        while True:
            ok, frame = await loop.run_in_executor(None, cap.read)
            if not ok:
                await asyncio.sleep(0.01)
                continue
            payload = await loop.run_in_executor(None, pipe.process, frame)
            payload["cam_id"] = args.cam or "noncalibrated"
            msg = json.dumps(payload)
            stale = []
            for ws in list(clients):
                try:
                    await ws.send(msg)
                except Exception:
                    stale.append(ws)
            for ws in stale:
                clients.discard(ws)
            now = time.time()
            if now - last_print > 2.0:
                print(f"[stream] frame {payload['frame_idx']:>5} "
                      f"fps {payload['fps']:5.1f} "
                      f"tracks {len(payload['tracks']):>2} "
                      f"clients {len(clients)}", flush=True)
                last_print = now
            if preview_win:
                debug = draw_debug(frame, payload)
                cv2.imshow(preview_win, debug)
                if (cv2.waitKey(1) & 0xFF) == ord("q"):
                    break

    async def handler(websocket):
        clients.add(websocket)
        peer = getattr(websocket, "remote_address", "?")
        print(f"[ws] 연결됨 {peer} (총 {len(clients)})", flush=True)
        try:
            async for _ in websocket:
                pass  # incoming msg 무시
        finally:
            clients.discard(websocket)
            print(f"[ws] 끊김 {peer} (남은 {len(clients)})", flush=True)

    print(f"[i] WebSocket 서버 ws://0.0.0.0:{args.port}", flush=True)
    async with serve(handler, "0.0.0.0", args.port):
        try:
            await producer()
        finally:
            cap.release()


def main() -> None:
    parser = argparse.ArgumentParser(description="실시간 카메라 → BEV 트랙")
    parser.add_argument("--cam", default=None, help="cam_id (호모그래피 파일명 키)")
    parser.add_argument("--source", default="0", help="카메라 인덱스 또는 비디오 경로")
    parser.add_argument("--model", default="yolo11n-pose.pt")
    parser.add_argument("--device", default=None, help="cpu / cuda:0 등 (자동 감지 기본)")
    parser.add_argument("--no-homography", action="store_true", help="캘리브레이션 없이 빠른 시연 모드")
    parser.add_argument("--serve", action="store_true", help="WebSocket 서버로 송출")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--preview", action="store_true", help="--serve 모드에서도 카메라 디버그 창 표시")
    args = parser.parse_args()

    if args.serve:
        asyncio.run(run_serve(args))
    else:
        run_local(args)


if __name__ == "__main__":
    main()
