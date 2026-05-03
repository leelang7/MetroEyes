"""비디오 파일을 마치 브라우저 카메라처럼 WebSocket(8765)으로 송출.

브라우저 카메라 대신 군중 영상 등을 BEV 파이프라인에 넣고 싶을 때.

사용:
  python scripts/feed_video.py                    # test/vtest.avi (기본)
  python scripts/feed_video.py path/to/clip.mp4
  python scripts/feed_video.py video.mp4 --fps 15 --port 8765
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent

# pythonw.exe (hidden) 환경에서 sys.stdout None이면 file로 redirect
if sys.stdout is None:
    _log = ROOT / "logs"
    _log.mkdir(exist_ok=True)
    sys.stdout = open(_log / "publisher.log", "a", encoding="utf-8", buffering=1)
    sys.stderr = sys.stdout


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", nargs="?", default=str(ROOT / "test" / "vtest.avi"))
    parser.add_argument("--url", default="ws://localhost:8765")
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--quality", type=int, default=70)
    parser.add_argument("--loop", action="store_true", default=True, help="끝나면 처음으로 (default)")
    parser.add_argument("--no-loop", dest="loop", action="store_false")
    args = parser.parse_args()

    from websockets.asyncio.client import connect

    interval = 1.0 / args.fps
    total_sent = 0
    print(f"[i] {args.video}  send_fps={args.fps}  → {args.url}  (auto-reconnect)")
    while True:
        cap = cv2.VideoCapture(args.video)
        if not cap.isOpened():
            print(f"[X] 비디오 열기 실패: {args.video}")
            sys.exit(1)
        try:
            async with connect(args.url, max_size=10 * 1024 * 1024,
                                ping_interval=30, ping_timeout=30) as ws:
                print(f"[i] WebSocket 연결 OK (총 송신 {total_sent})", flush=True)
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        if args.loop:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        return
                    ok2, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, args.quality])
                    if not ok2:
                        continue
                    await ws.send(jpg.tobytes())
                    total_sent += 1
                    if total_sent % 100 == 0:
                        print(f"  [tx] {total_sent} frames sent", flush=True)
                    await asyncio.sleep(interval)
        except (ConnectionError, OSError) as e:
            print(f"[!] 연결 끊김: {e}. 1초 후 재연결", flush=True)
        except Exception as e:
            print(f"[!] {type(e).__name__}: {e}. 1초 후 재연결", flush=True)
        finally:
            cap.release()
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
