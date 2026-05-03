"""Tesla식 multi-class BEV — YOLO11 GPU + 다중 클래스 + 트래킹.

검출 클래스 (COCO):
  person(0), bicycle(1), car(2), motorcycle(3), bus(5), truck(7)

브라우저 카메라 OR 영상 피더 → JPEG WebSocket → GPU YOLO + BoT-SORT → BEV broadcast.

실행:
  python -m src.cv.tesla_bev --port 8765
  python -m src.cv.tesla_bev --port 8765 --model yolo11s.pt --device cuda
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import time
from collections import deque

import cv2
import numpy as np
import torch
import torch.hub as _hub
_hub._check_repo_is_trusted = lambda *a, **kw: None   # MiDaS nested trust 우회

try:
    from ultralytics import YOLO
except ImportError as e:
    raise SystemExit("ultralytics 미설치. pip install ultralytics") from e


# COCO 클래스 매핑 (BEV에 의미 있는 것만)
CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    16: "dog",
    17: "cat",
}
CLASS_IDS = list(CLASSES.keys())


class Pipeline:
    def __init__(self, model_name: str = "yolo11n.pt", device: str | None = None,
                 conf: float = 0.30, imgsz: int = 640, homography_json: str | None = None,
                 use_depth_bev: bool = False):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        print(f"[load] {model_name} on {device}", flush=True)
        self.model = YOLO(model_name)
        self.model.to(device)
        dummy = np.zeros((imgsz, imgsz, 3), dtype=np.uint8)
        _ = self.model.predict(dummy, verbose=False, device=device)
        print(f"[load] {model_name} OK", flush=True)

        # 학습된 monocular depth (Tesla-like BEV 추출)
        self.use_depth_bev = use_depth_bev
        self.depth_model = None
        self.depth_transform = None
        if use_depth_bev:
            print(f"[load] MiDaS_small (depth-based BEV)...", flush=True)
            self.depth_model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small", trust_repo=True)
            self.depth_model.to(device).eval()
            transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
            self.depth_transform = transforms.small_transform
            print(f"[load] depth model OK", flush=True)

        self.conf = conf
        self.imgsz = imgsz
        self.fps_window: deque = deque(maxlen=30)
        self._last = time.time()
        self.frame_idx = 0

        # 호모그래피 (선택) — 진짜 BEV 거리 보존
        self.H = None
        self.H_image_size: tuple[int, int] | None = None
        if homography_json:
            try:
                with open(homography_json, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                src = np.asarray(cfg["image_points"], dtype=np.float32)
                dst = np.asarray(cfg["bev_points"], dtype=np.float32)
                self.H, _ = cv2.findHomography(src, dst, method=0)
                self.H_image_size = tuple(cfg.get("image_size", [0, 0]))
                print(f"[homography] {homography_json} loaded "
                      f"(image {self.H_image_size}, 4-point → BEV [0,1]²)", flush=True)
            except Exception as e:
                print(f"[homography] 로드 실패: {e}", flush=True)
                self.H = None

    @torch.no_grad()
    def _depth_map(self, frame_bgr: np.ndarray) -> np.ndarray:
        """MiDaS 모노 깊이 → 0~1 정규화 (가까움=1, 멀음=0)."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        inp = self.depth_transform(rgb).to(self.device)
        pred = self.depth_model(inp)
        depth = torch.nn.functional.interpolate(
            pred.unsqueeze(1), size=rgb.shape[:2], mode="bicubic", align_corners=False
        ).squeeze().cpu().numpy()
        d_min, d_max = depth.min(), depth.max()
        return (depth - d_min) / max(1e-6, d_max - d_min)

    def _project_to_bev(self, fx: float, fy: float, w: int, h: int,
                        H_override=None, H_size_override=None) -> tuple[float, float]:
        """이미지 픽셀 (fx, fy) → BEV 좌표. per-call override 지원."""
        H_use = H_override if H_override is not None else self.H
        size_use = H_size_override if H_size_override is not None else self.H_image_size
        if H_use is None:
            return fx / w, fy / h
        if size_use and size_use != (w, h):
            sx = size_use[0] / w
            sy = size_use[1] / h
            pt = np.array([[[fx * sx, fy * sy]]], dtype=np.float32)
        else:
            pt = np.array([[[fx, fy]]], dtype=np.float32)
        out = cv2.perspectiveTransform(pt, H_use)
        bx, by = float(out[0, 0, 0]), float(out[0, 0, 1])
        return max(0.0, min(1.0, bx)), max(0.0, min(1.0, by))

    def process_jpeg_with_homography(self, jpeg_bytes: bytes,
                                      H_per_client=None, H_size=None) -> dict | None:
        """클라이언트별 호모그래피로 처리."""
        # 임시 override 후 process_jpeg 호출
        saved_H, saved_size = self.H, self.H_image_size
        if H_per_client is not None:
            self.H, self.H_image_size = H_per_client, H_size
        try:
            return self.process_jpeg(jpeg_bytes)
        finally:
            self.H, self.H_image_size = saved_H, saved_size

    def process_jpeg(self, jpeg_bytes: bytes) -> dict | None:
        arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return None
        h, w = frame.shape[:2]
        # 큰 입력은 다운샘플 (속도/메모리)
        if w > 720:
            frame = cv2.resize(frame, (720, int(h * 720 / w)))
            h, w = frame.shape[:2]

        t = time.time()
        self.fps_window.append(t - self._last)
        self._last = t
        avg_dt = sum(self.fps_window) / max(1, len(self.fps_window))
        fps = 1.0 / max(avg_dt, 1e-3)

        # 학습 monocular depth (옵션)
        depth = self._depth_map(frame) if self.use_depth_bev else None

        # YOLO + BoT-SORT 트래킹
        results = self.model.track(
            frame, persist=True, verbose=False,
            classes=CLASS_IDS, conf=self.conf,
            device=self.device, imgsz=self.imgsz,
        )

        tracks = []
        debug_boxes = []
        if results and results[0].boxes is not None and results[0].boxes.id is not None:
            r = results[0]
            ids = r.boxes.id.int().cpu().tolist()
            cls = r.boxes.cls.int().cpu().tolist()
            conf_arr = r.boxes.conf.cpu().numpy()
            xyxy = r.boxes.xyxy.cpu().numpy()
            for i, tid in enumerate(ids):
                tid = int(tid)
                class_id = int(cls[i])
                class_name = CLASSES.get(class_id, "?")
                x1, y1, x2, y2 = xyxy[i]
                cx = (x1 + x2) / 2
                # 클래스별 ground 접점 보정 (입체 객체는 bbox 안쪽으로 push)
                if class_name in ("car", "bus", "truck"):
                    cy = y2 - (y2 - y1) * 0.35     # 차량 길이 절반 가까이 push
                elif class_name in ("motorcycle", "bicycle"):
                    cy = y2 - (y2 - y1) * 0.20
                else:
                    cy = y2

                if self.use_depth_bev and depth is not None:
                    # 학습 모노 깊이로 BEV 좌표 추출 (호모그래피 X)
                    # bbox 안 깊이 분포 (사용자 무관 자동) — 하위 30%만 평균 (지면 가까움)
                    yi1, yi2 = max(0, int(y1)), min(h, int(y2))
                    xi1, xi2 = max(0, int(x1)), min(w, int(x2))
                    crop = depth[yi1:yi2, xi1:xi2]
                    if crop.size > 0:
                        # 객체 발 영역 (하위 1/3)의 깊이 — 지면 접점 추정
                        bottom = crop[crop.shape[0] * 2 // 3:]
                        d_obj = float(np.median(bottom)) if bottom.size > 0 else float(np.median(crop))
                    else:
                        d_obj = 0.5
                    # BEV 좌표:
                    #   x = image x를 BEV로 (FOV 가정 단순)
                    #   y = 1 - depth (가까움=1, 멀음=0)
                    bev_x = float(cx) / w
                    bev_y = max(0.0, min(1.0, 1.0 - d_obj))
                    # 카메라 FOV 폭은 깊이에 비례 → 멀수록 좁음 (perspective 보정)
                    # cx의 0.5 중심 편차를 깊이만큼 축소
                    bev_x = 0.5 + (bev_x - 0.5) * (0.4 + 0.6 * (1 - bev_y))
                    bev_x = max(0.0, min(1.0, bev_x))
                else:
                    bev_x, bev_y = self._project_to_bev(float(cx), float(cy), w, h)
                tracks.append({
                    "id": tid,
                    "class": class_name,
                    "bev_x": bev_x,
                    "bev_y": bev_y,
                    "conf": float(conf_arr[i]),
                })
                debug_boxes.append({
                    "id": tid,
                    "class": class_name,
                    "x": float(x1 / w), "y": float(y1 / h),
                    "w": float((x2 - x1) / w), "h": float((y2 - y1) / h),
                })

        # 입력 frame echo (디버그용)
        ok_jpg, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 55])
        input_b64 = base64.b64encode(jpg.tobytes()).decode("ascii") if ok_jpg else ""

        self.frame_idx += 1
        return {
            "ts": t,
            "fps": fps,
            "frame_idx": self.frame_idx,
            "input_size": [w, h],
            "tracks": tracks,
            "debug_boxes": debug_boxes,
            "input_b64": input_b64,
            "device": self.device,
        }


def _to_int(v):
    try: return int(float(v)) if v not in (None, "") else None
    except Exception: return None

def _to_float(v):
    try: return float(v) if v not in (None, "") else None
    except Exception: return None


class OccupancyModel:
    """학습된 점유율 회귀 모델 + feature 컬럼 — joblib로 lazy load.

    추론: station 이름이 주어지면 cluster_assignments.csv에서 cluster id를 자동 lookup.
    """

    def __init__(self) -> None:
        self.model = None
        self.feature_cols: list[str] = []
        self.station_to_cluster: dict[str, str] = {}
        self._tried = False

    def _try_load(self) -> None:
        if self._tried:
            return
        self._tried = True
        try:
            import joblib
            import pandas as _pd
            from pathlib import Path
            root = Path(__file__).resolve().parents[2]
            mp = root / "outputs" / "models" / "occupancy_lgbm.joblib"
            fp = root / "outputs" / "models" / "feature_columns.json"
            cp = root / "outputs" / "cluster_assignments.csv"
            if not mp.exists() or not fp.exists():
                print(f"[occ-model] 모델 미발견 — 학습 후 사용 가능: {mp.relative_to(root)}", flush=True)
                return
            self.model = joblib.load(mp)
            import json as _json
            self.feature_cols = _json.loads(fp.read_text(encoding="utf-8"))
            if cp.exists():
                df = _pd.read_csv(cp)
                self.station_to_cluster = {
                    str(r["station"]): str(r["cluster"]) for _, r in df.iterrows()
                }
                print(f"[occ-model] 로드 OK · features={self.feature_cols} · stations={len(self.station_to_cluster)}",
                      flush=True)
            else:
                print(f"[occ-model] 로드 OK · features={self.feature_cols} (cluster CSV 없음)",
                      flush=True)
        except Exception as e:
            print(f"[occ-model] 로드 실패: {type(e).__name__}: {e}", flush=True)
            self.model = None

    def predict(self, hour: int, line: int, cluster_id: str | None,
                station: str | None = None) -> float | None:
        self._try_load()
        if self.model is None:
            return None
        try:
            # cluster_id 미지정 시 station에서 lookup
            if not cluster_id and station and station in self.station_to_cluster:
                cluster_id = self.station_to_cluster[station]
            row = {c: 0.0 for c in self.feature_cols}
            if "hour" in row: row["hour"] = float(hour)
            if "line" in row: row["line"] = float(line)
            if cluster_id is not None:
                ck = f"cluster_{cluster_id}"
                if ck in row: row[ck] = 1.0
            X = [[row[c] for c in self.feature_cols]]
            y = float(self.model.predict(X)[0])
            return max(0.0, min(1.05, y))
        except Exception as e:
            print(f"[occ-model] predict 실패: {type(e).__name__}: {e}", flush=True)
            return None


_OCC_MODEL = OccupancyModel()

async def run_serve(args) -> None:
    from websockets.asyncio.server import serve

    proc = Pipeline(model_name=args.model, device=args.device,
                    conf=args.conf, imgsz=args.imgsz,
                    homography_json=args.homography,
                    use_depth_bev=args.depth_bev)
    busy = {"flag": False}
    last_print = {"t": 0.0}
    rx = {"n": 0}
    clients: set = set()
    client_H: dict = {}   # ws → (H_matrix, (W, H))
    arrival_cache: dict = {}   # (station, line) → (ts, payload)
    ARRIVAL_TTL = 20.0
    population_cache: dict = {}   # poi → (ts, payload)
    POPULATION_TTL = 60.0   # 서울 실시간 도시데이터는 분 단위 갱신

    def _simulate_arrival_items(station: str, line: int | None) -> list[dict]:
        """API 응답이 비거나 ERROR-338(키 미등록) 시 시뮬 도착정보.
        실제 운행 패턴 근사: 평균 배차 ~3분, 다음 차편 4개.
        """
        import random as _rand
        rng = _rand.Random(hash((station, line, int(time.time() // 60))))
        base = rng.randint(30, 180)  # 첫 차편 30~180초
        items = []
        for i in range(4):
            sec = base + i * (180 + rng.randint(-30, 30))
            items.append({
                "subwayId": f"100{line}" if line else "1002",
                "subwayNm": f"{line or 2}호선",
                "trainLineNm": f"{station}행 - 다음 정거장 진입중",
                "bstatnNm": "잠실" if (line or 2) == 2 else "서울역",
                "arvlMsg2": ("당역 접근" if i == 0 and sec < 60 else f"{sec // 60}분 후"),
                "arvlMsg3": "전역 출발" if i == 0 else "전전역",
                "arvlCd": 1 if (i == 0 and sec < 60) else 2,
                "barvlDt": sec,
                "recptnDt": time.strftime("%Y-%m-%d %H:%M:%S"),
                "updnLine": "상행" if i % 2 == 0 else "하행",
            })
        return items

    async def fetch_arrival(station: str, line: int | None) -> dict:
        key = (station, line)
        now = time.time()
        cached = arrival_cache.get(key)
        if cached and now - cached[0] < ARRIVAL_TTL:
            return cached[1]
        loop = asyncio.get_running_loop()

        def _fetch_sync():
            try:
                from src.data_pipeline.seoul_opendata import SeoulOpenDataClient
                from src.utils.settings import load_config
                cfg = load_config("default").seoul_opendata
                base = getattr(cfg, "realtime_arrival_base", None) or cfg.base_url
                with SeoulOpenDataClient(base_url=base) as c:
                    return c.fetch("realtimeStationArrival", 0, 10, station)
            except Exception as e:
                return {"_error": f"{type(e).__name__}: {e}"}

        raw = await loop.run_in_executor(None, _fetch_sync)
        items_raw = raw.get("realtimeArrivalList") or []
        if line is not None:
            items_raw = [r for r in items_raw if r.get("subwayId") == f"100{line}"]
        rows = [{
            "subwayId": r.get("subwayId"),
            "subwayNm": r.get("subwayNm"),
            "trainLineNm": r.get("trainLineNm"),
            "bstatnNm": r.get("bstatnNm"),
            "arvlMsg2": r.get("arvlMsg2"),
            "arvlMsg3": r.get("arvlMsg3"),
            "arvlCd": r.get("arvlCd"),
            "barvlDt": r.get("barvlDt"),
            "recptnDt": r.get("recptnDt"),
            "updnLine": r.get("updnLine"),
        } for r in items_raw[:8]]

        err = raw.get("_error")
        # 실제 응답 비었거나 키 미등록 → 시뮬 fallback (데모 화면 비지 않게)
        simulated = False
        if not rows:
            rows = _simulate_arrival_items(station, line)
            simulated = True

        payload = {
            "type": "arrival",
            "station": station,
            "line": line,
            "items": rows,
            "fetched_at": now,
            "error": err,
            "simulated": simulated,
        }
        arrival_cache[key] = (now, payload)
        return payload

    async def broadcast(text: str, except_ws=None) -> None:
        stale = []
        for ws_c in list(clients):
            if ws_c is except_ws:
                continue
            try:
                await asyncio.wait_for(ws_c.send(text), timeout=0.5)
            except Exception:
                stale.append(ws_c)
        for ws_c in stale:
            clients.discard(ws_c)

    async def fetch_population(poi: str) -> dict:
        """서울 실시간 도시데이터 — POI 인구/혼잡도. 무료, 분 단위 갱신."""
        now = time.time()
        cached = population_cache.get(poi)
        if cached and now - cached[0] < POPULATION_TTL:
            return cached[1]
        loop = asyncio.get_running_loop()

        def _fetch_sync():
            try:
                from src.data_pipeline.seoul_opendata import SeoulOpenDataClient
                with SeoulOpenDataClient() as c:
                    return c.fetch("citydata_ppltn", 1, 5, poi)
            except Exception as e:
                return {"_error": f"{type(e).__name__}: {e}"}

        raw = await loop.run_in_executor(None, _fetch_sync)
        rows = raw.get("SeoulRtd.citydata_ppltn") or []
        row = rows[0] if rows else {}
        payload = {
            "type": "population",
            "poi": poi,
            "fetched_at": now,
            "area_nm": row.get("AREA_NM"),
            "area_cd": row.get("AREA_CD"),
            "congest_lvl": row.get("AREA_CONGEST_LVL"),  # 여유/보통/약간 붐빔/붐빔
            "congest_msg": row.get("AREA_CONGEST_MSG"),
            "ppltn_min": _to_int(row.get("AREA_PPLTN_MIN")),
            "ppltn_max": _to_int(row.get("AREA_PPLTN_MAX")),
            "male_rate": _to_float(row.get("MALE_PPLTN_RATE")),
            "female_rate": _to_float(row.get("FEMALE_PPLTN_RATE")),
            "resnt_rate": _to_float(row.get("RESNT_PPLTN_RATE")),
            "non_resnt_rate": _to_float(row.get("NON_RESNT_PPLTN_RATE")),
            "ppltn_time": row.get("PPLTN_TIME"),
            "error": raw.get("_error"),
        }
        population_cache[poi] = (now, payload)
        return payload

    async def _reply_arrival(websocket, station: str, line, peer) -> None:
        try:
            payload = await fetch_arrival(station, line)
            await asyncio.wait_for(websocket.send(json.dumps(payload)), timeout=2.0)
            cnt = len(payload.get("items") or [])
            err = payload.get("error")
            tag = f"err={err}" if err else f"items={cnt}"
            print(f"[arrival] {peer} {station} line={line} {tag}", flush=True)
        except Exception as e:
            print(f"[arrival] {peer} fail: {type(e).__name__}: {e}", flush=True)

    async def _reply_predict(websocket, hour: int, line: int,
                              cluster_id, station_name, peer) -> None:
        try:
            loop = asyncio.get_running_loop()
            y = await loop.run_in_executor(
                None, _OCC_MODEL.predict, hour, line, cluster_id, station_name
            )
            payload = {
                "type": "occupancy_predict",
                "hour": hour, "line": line,
                "cluster": cluster_id, "stationName": station_name,
                "predicted": y,
                "available": y is not None,
            }
            await asyncio.wait_for(websocket.send(json.dumps(payload)), timeout=2.0)
            print(f"[predict] {peer} h={hour} L{line} c={cluster_id} st={station_name} → {y}", flush=True)
        except Exception as e:
            print(f"[predict] {peer} fail: {type(e).__name__}: {e}", flush=True)

    async def _reply_population(websocket, poi: str, peer) -> None:
        try:
            payload = await fetch_population(poi)
            await asyncio.wait_for(websocket.send(json.dumps(payload)), timeout=2.0)
            err = payload.get("error")
            lvl = payload.get("congest_lvl")
            n = payload.get("ppltn_max")
            tag = f"err={err}" if err else f"{lvl} ~{n}"
            print(f"[ppltn] {peer} {poi} {tag}", flush=True)
        except Exception as e:
            print(f"[ppltn] {peer} fail: {type(e).__name__}: {e}", flush=True)

    async def handler(websocket):
        peer = getattr(websocket, "remote_address", "?")
        clients.add(websocket)
        print(f"[ws] 연결 {peer} (총 {len(clients)})", flush=True)
        try:
            async for msg in websocket:
                # text 메시지 = 컨트롤 (호모그래피 set 등)
                if isinstance(msg, str):
                    try:
                        ctrl = json.loads(msg)
                        ctype = ctrl.get("type")
                        if ctype == "set_homography":
                            if ctrl.get("clear"):
                                client_H.pop(websocket, None)
                                print(f"[ctrl] {peer} homography 해제", flush=True)
                            else:
                                src = np.asarray(ctrl["image_points"], dtype=np.float32)
                                dst = np.asarray(ctrl["bev_points"], dtype=np.float32)
                                H, _ = cv2.findHomography(src, dst, method=0)
                                size = tuple(ctrl.get("image_size", [0, 0]))
                                client_H[websocket] = (H, size)
                                print(f"[ctrl] {peer} homography set image={size}", flush=True)
                        elif ctype == "arrival_query":
                            station = (ctrl.get("stationName") or "잠실").strip()
                            line = ctrl.get("line")
                            asyncio.create_task(_reply_arrival(websocket, station, line, peer))
                        elif ctype == "population_query":
                            poi = (ctrl.get("poi") or "강남역").strip()
                            asyncio.create_task(_reply_population(websocket, poi, peer))
                        elif ctype == "predict_occupancy":
                            hour = int(ctrl.get("hour", 18))
                            line = int(ctrl.get("line", 2))
                            cluster_id = ctrl.get("cluster")
                            station_name = ctrl.get("stationName")
                            asyncio.create_task(_reply_predict(websocket, hour, line,
                                                                cluster_id, station_name, peer))
                    except Exception as e:
                        print(f"[ctrl] {peer} parse fail: {e}", flush=True)
                    continue
                if not isinstance(msg, (bytes, bytearray)):
                    continue
                rx["n"] += 1
                if busy["flag"]:
                    continue
                busy["flag"] = True
                try:
                    loop = asyncio.get_running_loop()
                    H_size = client_H.get(websocket, (None, None))
                    result = await loop.run_in_executor(
                        None, proc.process_jpeg_with_homography,
                        bytes(msg), H_size[0], H_size[1])
                    if result:
                        await broadcast(json.dumps(result))   # sender 포함 모두 (timeout으로 hang 방지)
                    now = time.time()
                    if now - last_print["t"] > 1.0 and result:
                        cls_breakdown = {}
                        for t in result["tracks"]:
                            cls_breakdown[t["class"]] = cls_breakdown.get(t["class"], 0) + 1
                        cls_str = " ".join(f"{k}:{v}" for k, v in cls_breakdown.items()) or "-"
                        print(f"[rx] frame={rx['n']} tracks={len(result['tracks'])} "
                              f"[{cls_str}] fps={result['fps']:.1f} clients={len(clients)} "
                              f"dev={result['device']}", flush=True)
                        last_print["t"] = now
                finally:
                    busy["flag"] = False
        finally:
            clients.discard(websocket)
            print(f"[ws] 끊김 {peer} (남은 {len(clients)})", flush=True)

    print(f"[i] BEV multi-class (YOLO {args.model}) ws://0.0.0.0:{args.port}", flush=True)
    async with serve(handler, "0.0.0.0", args.port, max_size=10 * 1024 * 1024):
        await asyncio.Future()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--device", default=None, help="cuda / cpu / auto")
    parser.add_argument("--conf", type=float, default=0.30)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--homography", default=None, help="configs/homography_*.json 경로")
    parser.add_argument("--depth-bev", action="store_true",
                        help="MiDaS monocular depth로 BEV 좌표 추출 (Tesla-like, 호모그래피 X)")
    args = parser.parse_args()
    asyncio.run(run_serve(args))


if __name__ == "__main__":
    main()
