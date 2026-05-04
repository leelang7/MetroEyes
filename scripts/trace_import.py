"""백엔드 모듈 import 어디서 막히는지 단계별 출력."""
import sys, os, time
print("[1] python start", flush=True)
print(f"    cwd={os.getcwd()}", flush=True)
print(f"    sys.executable={sys.executable}", flush=True)

t0 = time.time()
print("[2] importing cv2 ...", flush=True)
import cv2
print(f"    cv2 {cv2.__version__} in {time.time()-t0:.1f}s", flush=True)

t0 = time.time()
print("[3] importing torch ...", flush=True)
import torch
print(f"    torch {torch.__version__} cuda={torch.cuda.is_available()} in {time.time()-t0:.1f}s", flush=True)

t0 = time.time()
print("[4] importing ultralytics ...", flush=True)
from ultralytics import YOLO
print(f"    ultralytics ok in {time.time()-t0:.1f}s", flush=True)

t0 = time.time()
print("[5] loading yolo11n.pt ...", flush=True)
m = YOLO("yolo11n.pt")
print(f"    model loaded in {time.time()-t0:.1f}s", flush=True)

t0 = time.time()
print("[6] importing src.cv.tesla_bev ...", flush=True)
from src.cv import tesla_bev
print(f"    tesla_bev ok in {time.time()-t0:.1f}s", flush=True)

print("[7] ALL OK — backend should be able to start.", flush=True)
