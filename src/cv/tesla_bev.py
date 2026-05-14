"""Tesla식 multi-class BEV — YOLO11 GPU + 다중 클래스 + 트래킹.

검출 클래스 (COCO):
  person(0), bicycle(1), car(2), motorcycle(3), bus(5), truck(7)

브라우저 카메라 OR 영상 피더 → JPEG WebSocket → GPU YOLO + BoT-SORT → BEV broadcast.

실행:
  python -m src.cv.tesla_bev --port 8765
  python -m src.cv.tesla_bev --port 8765 --model yolo11n.pt --device cuda
"""
from __future__ import annotations

import os
import sys

# pythonw.exe (콘솔 없음) 환경에서 stdout이 None이면 file로 자동 redirect.
if sys.stdout is None:
    _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _log = os.path.join(_root, "logs")
    os.makedirs(_log, exist_ok=True)
    sys.stdout = open(os.path.join(_log, "backend.log"), "a", encoding="utf-8", buffering=1)
    sys.stderr = sys.stdout

import argparse
import asyncio
import base64
import json
import re
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
    # 단일 active source 정책
    # claimed: 명시적으로 claim한 client (운영자 콘솔의 영상 송신). 우선권.
    # 명시 claim 없으면 가장 최근 송신자가 5초 TTL로 active.
    active_source = {"ws": None, "until": 0.0, "claimed": False}
    ACTIVE_SOURCE_TTL = 5.0
    clients: set = set()
    client_H: dict = {}   # ws → (H_matrix, (W, H))
    arrival_cache: dict = {}   # (station, line) → (ts, payload)
    ARRIVAL_TTL = 20.0
    population_cache: dict = {}   # poi → (ts, payload)
    POPULATION_TTL = 60.0   # 서울 실시간 도시데이터는 분 단위 갱신
    citydata_cache: dict = {}     # poi → (ts, payload)  통합 도시데이터 (버스/도로/주차/따릉이/날씨)
    CITYDATA_TTL = 60.0
    events_cache: dict = {}        # poi → (ts, list)  주변 문화 행사 — 인구 예측 신호
    EVENTS_TTL = 600.0  # 10분 (행사는 자주 안 바뀜)
    # POI별 lat/lon 매핑 — 행사 거리 필터에 사용
    POI_COORD = {
        "잠실역": (37.5133, 127.1000), "강남역": (37.4980, 127.0276),
        "홍대 관광특구": (37.5572, 126.9244), "광화문·덕수궁": (37.5717, 126.9766),
        "서울역": (37.5547, 126.9707), "종로·청계 관광특구": (37.5717, 126.9914),
        "신촌·이대역": (37.5556, 126.9362), "사당역": (37.4766, 126.9817),
        "건대입구역": (37.5403, 127.0703), "김포공항": (37.5615, 126.8014),
        "잠실종합운동장": (37.5159, 127.0731), "잠실한강공원": (37.5180, 127.0822),
        # 성수동/서울숲 라인 — 인파 폭증 핫스팟 (citydata_ppltn 110 POI 포함)
        "성수카페거리": (37.5446, 127.0556),
        "서울숲공원": (37.5443, 127.0374),
        "뚝섬한강공원": (37.5295, 127.0708),
        "성수역": (37.5444, 127.0557),
    }
    # (I2) 사회적 임팩트 — 시민이 권장 칸 탑승 누를 때 누적
    impact_state = {
        "events": [],            # 최근 200개 이벤트 (ts, station, saved_pct)
        "total_count": 0,
        "saved_pct_sum": 0.0,
    }
    IMPACT_MAX = 200
    # 사고/이벤트 누적 — realbev/operator 시연 모드 incident_log 송신 시
    incident_state = {
        "emergency": 0, "suspicious": 0, "lost": 0, "free_ride": 0,
        "priority_seat": 0, "bottleneck": 0,
        "events": [],   # 최근 50개
    }
    INCIDENT_KEEP = 50

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
                from src.utils.settings import load_config, load_env
                cfg = load_config("default").seoul_opendata
                env = load_env()
                base = getattr(cfg, "realtime_arrival_base", None) or cfg.base_url
                # 도착정보는 별도 키가 있으면 그걸 우선 사용 (서울 OpenAPI는 키 단위 서비스 등록)
                key = env.seoul_subway_arrival_key or env.seoul_opendata_api_key
                with SeoulOpenDataClient(api_key=key, base_url=base) as c:
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

    # === 인파 폭증 컨텍스트 캐시 (네이버 뉴스 + LLM) ===
    context_cache: dict = {}    # poi → (ts, payload)
    CONTEXT_TTL = 600.0         # 10분 — 뉴스는 자주 안 바뀜
    ppltn_history: dict = {}    # poi → [(ts, mid)] — 폭증 추세 추적
    PPLTN_HIST_MAX = 12

    async def fetch_context_news(poi: str) -> dict:
        """인파 폭증 시 자동 호출 — 네이버 뉴스/블로그 검색 + 옵셔널 LLM 요약.

        흐름: citydata_ppltn 폭증 감지 → 이 함수 → "왜 붐비는지" 컨텍스트 broadcast.
        키 없으면 graceful fallback (검색량 / 행사 데이터로 추정).
        """
        now = time.time()
        cached = context_cache.get(poi)
        if cached and now - cached[0] < CONTEXT_TTL:
            return cached[1]
        loop = asyncio.get_running_loop()

        def _fetch_naver_news() -> list[dict]:
            """네이버 검색 API — 최근 뉴스 5건."""
            cid = os.environ.get("NAVER_CLIENT_ID", "")
            csec = os.environ.get("NAVER_CLIENT_SECRET", "")
            if not cid or not csec:
                return []
            try:
                import urllib.request, urllib.parse, json as _json
                # POI에서 행정동·랜드마크명 추출 (예: "성수카페거리" → "성수동")
                query_parts = [poi]
                if "성수" in poi: query_parts.append("성수동")
                if "서울숲" in poi: query_parts.append("서울숲")
                if "뚝섬" in poi: query_parts.append("뚝섬")
                if "홍대" in poi: query_parts.append("홍대")
                if "강남" in poi: query_parts.append("강남역")
                query = " ".join(query_parts[:1]) + " 인파"
                url = "https://openapi.naver.com/v1/search/news.json?" + urllib.parse.urlencode({
                    "query": query, "display": 5, "sort": "date",
                })
                req = urllib.request.Request(url, headers={
                    "X-Naver-Client-Id": cid,
                    "X-Naver-Client-Secret": csec,
                })
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = _json.loads(resp.read().decode("utf-8"))
                items = []
                for it in data.get("items", [])[:5]:
                    # HTML 태그 제거
                    title = re.sub(r"<[^>]+>", "", it.get("title", "")).replace("&quot;", '"').replace("&amp;", "&")
                    desc = re.sub(r"<[^>]+>", "", it.get("description", ""))[:100]
                    items.append({
                        "title": title, "desc": desc,
                        "link": it.get("link", ""), "pubDate": it.get("pubDate", ""),
                    })
                return items
            except Exception:
                return []

        def _summarize_with_llm(news_items: list, poi: str, congest: str) -> str:
            """Anthropic Claude 로 뉴스 핵심 요약 → '왜 붐비는지' 한 줄.
            키 없으면 단순 키워드 추출 fallback."""
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not api_key or not news_items:
                # Fallback: 헤드라인 1개 그대로
                if news_items:
                    return f"최근 뉴스: {news_items[0]['title'][:60]}"
                return f"{poi} {congest} — 행사·날씨·환승 영향 가능"
            try:
                import urllib.request, json as _json
                titles = "\n".join(f"- {it['title']}" for it in news_items[:5])
                prompt = (f"{poi} 지역 인파가 '{congest}' 등급입니다. 다음 뉴스 헤드라인을 보고 "
                          f"'왜 붐비는지' 한 줄로 답하세요 (40자 이내, 행사·시즌·이벤트 키워드 우선):\n{titles}")
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=_json.dumps({
                        "model": "claude-haiku-4-5",
                        "max_tokens": 80,
                        "messages": [{"role": "user", "content": prompt}],
                    }).encode("utf-8"),
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=6) as resp:
                    j = _json.loads(resp.read().decode("utf-8"))
                txt = j.get("content", [{}])[0].get("text", "").strip()
                return txt[:80] if txt else news_items[0]["title"][:60]
            except Exception:
                return news_items[0]["title"][:60] if news_items else f"{poi} {congest}"

        news = await loop.run_in_executor(None, _fetch_naver_news)
        summary = await loop.run_in_executor(None, _summarize_with_llm, news, poi, "")
        payload = {
            "type": "context",
            "poi": poi,
            "fetched_at": now,
            "summary": summary,
            "news": news,
            "sources": {
                "naver": bool(news) and bool(os.environ.get("NAVER_CLIENT_ID")),
                "llm":   bool(os.environ.get("ANTHROPIC_API_KEY")),
            },
        }
        context_cache[poi] = (now, payload)
        return payload

    async def fetch_population(poi: str) -> dict:
        """서울 실시간 도시데이터 — POI 인구/혼잡도. 무료, 분 단위 갱신.
        폭증 감지 시 fetch_context_news() 자동 트리거 → broadcast."""
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

        # === 폭증 감지 → 컨텍스트 broadcast ===
        mid = ((payload.get("ppltn_min") or 0) + (payload.get("ppltn_max") or 0)) / 2
        if mid > 0:
            hist = ppltn_history.setdefault(poi, [])
            hist.append((now, mid))
            if len(hist) > PPLTN_HIST_MAX: hist.pop(0)
            # 폭증 = 붐빔 OR (약간 붐빔 + 직전 대비 +5% 상승)
            lvl = payload.get("congest_lvl") or ""
            surge = lvl == "붐빔"
            if not surge and lvl == "약간 붐빔" and len(hist) >= 2:
                prev = hist[-2][1]
                surge = prev > 0 and (mid - prev) / prev > 0.05
            if surge:
                ctx = await fetch_context_news(poi)
                ctx["trigger"] = {"poi": poi, "lvl": lvl, "ppltn": int(mid)}
                # 모든 client 에 broadcast (시민/운영자 동시 수신)
                asyncio.create_task(broadcast(json.dumps(ctx, ensure_ascii=False)))
        return payload

    def _haversine_km(lat1, lon1, lat2, lon2):
        import math
        R = 6371.0
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    async def fetch_events(poi: str, radius_km: float = 1.5) -> dict:
        """주변 문화 행사 — 인구 폭증 예측 신호."""
        now = time.time()
        cached = events_cache.get(poi)
        if cached and now - cached[0] < EVENTS_TTL:
            return cached[1]
        loop = asyncio.get_running_loop()

        def _fetch_sync():
            try:
                from src.data_pipeline.seoul_opendata import SeoulOpenDataClient
                with SeoulOpenDataClient() as c:
                    # 행사 1~200 fetch
                    return c.fetch("ListPublicReservationCulture", 1, 200)
            except Exception as e:
                return {"_error": f"{type(e).__name__}: {e}"}

        raw = await loop.run_in_executor(None, _fetch_sync)
        rows = (raw.get("ListPublicReservationCulture") or {}).get("row") or []
        coord = POI_COORD.get(poi)
        nearby = []
        for r in rows:
            try:
                x = float(r.get("X")); y = float(r.get("Y"))  # X=lon, Y=lat
            except Exception:
                continue
            if coord:
                d = _haversine_km(coord[0], coord[1], y, x)
                if d > radius_km: continue
            else:
                d = None
            # 종료 안 된 행사만
            stat = r.get("SVCSTATNM") or ""
            if stat in ("접수종료", "운영종료"): continue
            nearby.append({
                "name": r.get("SVCNM"),
                "place": r.get("PLACENM"),
                "status": stat,
                "open_begin": r.get("SVCOPNBGNDT"),
                "open_end": r.get("SVCOPNENDDT"),
                "tgt": r.get("USETGTINFO"),
                "v_max": _to_int(r.get("V_MAX")),
                "area": r.get("AREANM"),
                "url": r.get("SVCURL"),
                "tel": r.get("TELNO"),
                "lat": y, "lon": x, "dist_km": round(d, 2) if d is not None else None,
            })
        # 거리 가까운 + capacity 큰 순으로 정렬
        nearby.sort(key=lambda e: (e.get("dist_km") or 999, -(e.get("v_max") or 0)))
        nearby = nearby[:10]
        # 인구 영향 예상치 — 가까운 큰 행사 v_max 합
        total_capacity = sum(e.get("v_max") or 0 for e in nearby)
        payload = {
            "type": "events",
            "poi": poi,
            "fetched_at": now,
            "events": nearby,
            "total_count": len(nearby),
            "total_capacity": total_capacity,
            "error": raw.get("_error"),
        }
        events_cache[poi] = (now, payload)
        return payload

    async def _reply_model_metrics(websocket, peer) -> None:
        """학습된 ML 모델 검증 메트릭 — outputs/occupancy_metrics.json 읽어 응답."""
        try:
            from pathlib import Path as _P
            import json as _json
            root = _P(__file__).resolve().parents[2]
            mp = root / "outputs" / "occupancy_metrics.json"
            if not mp.exists():
                payload = {"type": "model_metrics", "available": False,
                           "reason": "outputs/occupancy_metrics.json 없음 — scripts/train_occupancy.py 실행 필요"}
            else:
                metrics = _json.loads(mp.read_text(encoding="utf-8"))
                payload = {"type": "model_metrics", "available": True, **metrics}
            await asyncio.wait_for(websocket.send(json.dumps(payload, ensure_ascii=False)), timeout=2.0)
        except Exception as e:
            print(f"[metrics] {peer} fail: {type(e).__name__}: {e}", flush=True)

    async def _reply_events(websocket, poi: str, peer) -> None:
        try:
            payload = await fetch_events(poi)
            await asyncio.wait_for(websocket.send(json.dumps(payload, ensure_ascii=False)), timeout=2.0)
            print(f"[events] {peer} {poi} count={payload['total_count']} cap={payload['total_capacity']}", flush=True)
        except Exception as e:
            print(f"[events] {peer} fail: {type(e).__name__}: {e}", flush=True)

    async def fetch_citydata(poi: str) -> dict:
        """서울 실시간 도시데이터 통합 — 한 호출로 인구/버스/도로/주차/따릉이/날씨/상권."""
        now = time.time()
        cached = citydata_cache.get(poi)
        if cached and now - cached[0] < CITYDATA_TTL:
            return cached[1]
        loop = asyncio.get_running_loop()

        def _fetch_sync():
            try:
                from src.data_pipeline.seoul_opendata import SeoulOpenDataClient
                with SeoulOpenDataClient() as c:
                    return c.fetch("citydata", 1, 5, poi)
            except Exception as e:
                return {"_error": f"{type(e).__name__}: {e}"}

        raw = await loop.run_in_executor(None, _fetch_sync)
        cd = raw.get("CITYDATA") or {}
        # 핵심 메트릭만 정규화 — 응답 자체는 매우 큼, 폰/UI에 필요한 것만 추림
        ppltn = (cd.get("LIVE_PPLTN_STTS") or [{}])[0] if isinstance(cd.get("LIVE_PPLTN_STTS"), list) else cd.get("LIVE_PPLTN_STTS") or {}
        weather = (cd.get("WEATHER_STTS") or [{}])[0] if cd.get("WEATHER_STTS") else {}
        sub_ppltn = cd.get("LIVE_SUB_PPLTN") or {}
        bus_ppltn = cd.get("LIVE_BUS_PPLTN") or {}
        cmrcl = cd.get("LIVE_CMRCL_STTS") or {}
        road = cd.get("ROAD_TRAFFIC_STTS") or {}
        road_avg = (road.get("AVG_ROAD_DATA") if isinstance(road, dict) else None) or {}
        prk_list = cd.get("PRK_STTS") or []
        sbike_list = cd.get("SBIKE_STTS") or []

        # 따릉이/주차 — 가까운 N개만, 핵심 필드만
        sbike = [{
            "name": s.get("SBIKE_SPOT_NM"), "shared": _to_int(s.get("SBIKE_SHARED")),
            "rack": _to_int(s.get("SBIKE_RACK_CNT")), "parking": _to_int(s.get("SBIKE_PARKING_CNT")),
        } for s in sbike_list[:5]]
        parking = [{
            "name": p.get("PRK_NM"), "type": p.get("PRK_TYPE"),
            "cap": _to_int(p.get("CPCTY")), "cur": _to_int(p.get("CUR_PRK_CNT")),
        } for p in prk_list[:5]]

        # 도로 65개 list → 가장 느린/빠른 5개씩만 (UI용)
        roads_all = []
        rt = cd.get("ROAD_TRAFFIC_STTS")
        if isinstance(rt, dict):
            roads_all = rt.get("ROAD_TRAFFIC_STTS") or []
        _road_link_count = len(roads_all) if isinstance(roads_all, list) else 0
        roads_with_spd = []
        for r in (roads_all or []):
            spd = _to_float(r.get("SPD"))
            if spd is None:
                continue
            roads_with_spd.append({
                "name": r.get("ROAD_NM"),
                "spd": spd,
                "idx": r.get("IDX"),
                "from": r.get("START_ND_NM"),
                "to": r.get("END_ND_NM"),
            })
        roads_with_spd.sort(key=lambda x: x["spd"])
        _roads_slow = roads_with_spd[:5]
        _roads_fast = list(reversed(roads_with_spd[-5:])) if roads_with_spd else []

        # 24시간 예보 — 향후 6시간 + 강수 시각만 추림 (UI 한 줄 표시용)
        fcst_raw = weather.get("FCST24HOURS") or []
        fcst = []
        rain_first = None  # 첫 강수 예보 시각
        for f in fcst_raw[:24]:
            row = {
                "dt": f.get("FCST_DT"),
                "temp": _to_int(f.get("TEMP")),
                "precpt_type": f.get("PRECPT_TYPE"),
                "rain_chance": _to_int(f.get("RAIN_CHANCE")),
                "sky": f.get("SKY_STTS"),
            }
            fcst.append(row)
            if rain_first is None and (f.get("PRECPT_TYPE") in ("비", "눈", "비/눈", "소나기")):
                rain_first = {"dt": f.get("FCST_DT"), "type": f.get("PRECPT_TYPE")}

        # 상권 카테고리별 — 핵심만
        rsb = cmrcl.get("CMRCL_RSB") or []
        rsb_brief = [{
            "ctgr": r.get("RSB_MID_CTGR"),
            "lvl": r.get("RSB_PAYMENT_LVL"),
            "cnt": _to_int(r.get("RSB_SH_PAYMENT_CNT")),
        } for r in rsb[:6]]

        payload = {
            "type": "citydata",
            "poi": poi,
            "fetched_at": now,
            # 인구·혼잡 (citydata_ppltn과 동일하지만 통합 호출에 포함)
            "area_nm": ppltn.get("AREA_NM"), "area_cd": ppltn.get("AREA_CD"),
            "congest_lvl": ppltn.get("AREA_CONGEST_LVL"),
            "ppltn_min": _to_int(ppltn.get("AREA_PPLTN_MIN")),
            "ppltn_max": _to_int(ppltn.get("AREA_PPLTN_MAX")),
            "ppltn_time": ppltn.get("PPLTN_TIME"),
            # 지하철·버스 라이브 승하차 (5/10/30분 누적)
            "sub_5wthn_gton_max": _to_int(sub_ppltn.get("SUB_5WTHN_GTON_PPLTN_MAX")),
            "sub_10wthn_gton_max": _to_int(sub_ppltn.get("SUB_10WTHN_GTON_PPLTN_MAX")),
            "sub_30wthn_gton_max": _to_int(sub_ppltn.get("SUB_30WTHN_GTON_PPLTN_MAX")),
            "sub_acml_gton_max": _to_int(sub_ppltn.get("SUB_ACML_GTON_PPLTN_MAX")),
            "sub_stn_cnt": _to_int(sub_ppltn.get("SUB_STN_CNT")),
            "bus_5wthn_gton_max": _to_int(bus_ppltn.get("BUS_5WTHN_GTON_PPLTN_MAX")),
            "bus_10wthn_gton_max": _to_int(bus_ppltn.get("BUS_10WTHN_GTON_PPLTN_MAX")),
            "bus_30wthn_gton_max": _to_int(bus_ppltn.get("BUS_30WTHN_GTON_PPLTN_MAX")),
            "bus_acml_gton_max": _to_int(bus_ppltn.get("BUS_ACML_GTON_PPLTN_MAX")),
            "bus_stn_cnt": _to_int(bus_ppltn.get("BUS_STN_CNT")),
            # 도로 평균
            "road_avg_speed": _to_float(road_avg.get("ROAD_TRAFFIC_SPD")),
            "road_avg_idx": road_avg.get("ROAD_TRAFFIC_IDX"),
            "road_msg": road_avg.get("ROAD_MSG"),
            "road_link_cnt": _road_link_count,
            "roads_slow": _roads_slow,
            "roads_fast": _roads_fast,
            # 날씨 (현재)
            "temp": _to_float(weather.get("TEMP")),
            "sensible_temp": _to_float(weather.get("SENSIBLE_TEMP")),
            "max_temp": _to_float(weather.get("MAX_TEMP")),
            "min_temp": _to_float(weather.get("MIN_TEMP")),
            "humidity": _to_float(weather.get("HUMIDITY")),
            "wind_dirct": weather.get("WIND_DIRCT"),
            "wind_spd": _to_float(weather.get("WIND_SPD")),
            "precpt_type": weather.get("PRECPT_TYPE"),
            "pcp_msg": weather.get("PCP_MSG"),
            "weather_time": weather.get("WEATHER_TIME"),
            # 공기질
            "pm25": _to_int(weather.get("PM25")),
            "pm25_idx": weather.get("PM25_INDEX"),
            "pm10": _to_int(weather.get("PM10")),
            "pm10_idx": weather.get("PM10_INDEX"),
            "air_idx": weather.get("AIR_IDX"),
            "air_idx_mvl": _to_float(weather.get("AIR_IDX_MVL")),
            "air_msg": weather.get("AIR_MSG"),
            # 자외선
            "uv_lvl": _to_int(weather.get("UV_INDEX_LVL")),
            "uv_idx": weather.get("UV_INDEX"),
            "uv_msg": weather.get("UV_MSG"),
            "sunrise": weather.get("SUNRISE"),
            "sunset": weather.get("SUNSET"),
            # 24시간 예보 (강수 시각 first)
            "fcst": fcst,
            "rain_first": rain_first,
            # 환승 옵션
            "sbike": sbike,
            "parking": parking,
            # 상권 결제
            "cmrcl_lvl": cmrcl.get("AREA_CMRCL_LVL"),
            "cmrcl_payment_cnt": _to_int(cmrcl.get("AREA_SH_PAYMENT_CNT")),
            "cmrcl_male_rate": _to_float(cmrcl.get("CMRCL_MALE_RATE")),
            "cmrcl_female_rate": _to_float(cmrcl.get("CMRCL_FEMALE_RATE")),
            "cmrcl_rsb": rsb_brief,
            # 안전 알림
            "events": cd.get("EVENT_STTS") or [],
            "alerts": cd.get("LIVE_DST_MESSAGE") or [],
            "accidents": cd.get("ACDNT_CNTRL_STTS") or [],
            "error": raw.get("_error"),
        }
        citydata_cache[poi] = (now, payload)
        return payload

    async def _send_impact_to(ws_c) -> None:
        n = impact_state["total_count"]
        avg_saved = (impact_state["saved_pct_sum"] / n) if n > 0 else 0.0
        payload = {
            "type": "impact_summary",
            "total_count": n,
            "avg_saved_pct": avg_saved,
            "recent": impact_state["events"][-10:],
            "ts": time.time(),
        }
        try:
            await asyncio.wait_for(ws_c.send(json.dumps(payload, ensure_ascii=False)), timeout=1.0)
        except Exception:
            pass

    async def _broadcast_impact() -> None:
        """누적 임팩트 요약을 모든 client에 broadcast."""
        n = impact_state["total_count"]
        avg_saved = (impact_state["saved_pct_sum"] / n) if n > 0 else 0.0
        recent = impact_state["events"][-10:]
        payload = {
            "type": "impact_summary",
            "total_count": n,
            "avg_saved_pct": avg_saved,
            "recent": recent,
            "ts": time.time(),
        }
        await broadcast(json.dumps(payload, ensure_ascii=False))

    async def _reply_citydata(websocket, poi: str, peer) -> None:
        try:
            payload = await fetch_citydata(poi)
            await asyncio.wait_for(websocket.send(json.dumps(payload, ensure_ascii=False)), timeout=2.0)
            err = payload.get("error")
            tag = f"err={err}" if err else f"{payload.get('congest_lvl')} bus30={payload.get('bus_30wthn_gton_max')} bike={len(payload.get('sbike') or [])}"
            print(f"[citydata] {peer} {poi} {tag}", flush=True)
        except Exception as e:
            print(f"[citydata] {peer} fail: {type(e).__name__}: {e}", flush=True)

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
        # 새 client에 현재 임팩트 요약 즉시 전달
        if impact_state["total_count"] > 0:
            asyncio.create_task(_send_impact_to(websocket))
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
                        elif ctype == "citydata_query":
                            poi = (ctrl.get("poi") or "강남역").strip()
                            asyncio.create_task(_reply_citydata(websocket, poi, peer))
                        elif ctype == "events_query":
                            poi = (ctrl.get("poi") or "강남역").strip()
                            asyncio.create_task(_reply_events(websocket, poi, peer))
                        elif ctype == "model_metrics_query":
                            asyncio.create_task(_reply_model_metrics(websocket, peer))
                        elif ctype == "claim_active":
                            # 명시 claim — 이 client만 frame 처리, 다른 source 무시
                            active_source["ws"] = websocket
                            active_source["claimed"] = True
                            print(f"[src] CLAIMED by {peer}", flush=True)
                        elif ctype == "release_active":
                            if active_source["ws"] is websocket and active_source["claimed"]:
                                active_source["claimed"] = False
                                active_source["until"] = 0.0
                                print(f"[src] released by {peer}", flush=True)
                        elif ctype == "impact_log":
                            # 시민 PWA/폰이 "탑승하기" 누를 때
                            saved = float(ctrl.get("saved_pct") or 0)
                            impact_state["events"].append({
                                "ts": time.time(),
                                "station": ctrl.get("station") or "",
                                "car": ctrl.get("car") or "",
                                "saved_pct": saved,
                            })
                            if len(impact_state["events"]) > IMPACT_MAX:
                                impact_state["events"] = impact_state["events"][-IMPACT_MAX:]
                            impact_state["total_count"] += 1
                            impact_state["saved_pct_sum"] += saved
                            # 모든 client에 누적 요약 broadcast (운영자 콘솔이 받음)
                            asyncio.create_task(_broadcast_impact())
                        elif ctype == "predict_occupancy":
                            hour = int(ctrl.get("hour", 18))
                            line = int(ctrl.get("line", 2))
                            cluster_id = ctrl.get("cluster")
                            station_name = ctrl.get("stationName")
                            asyncio.create_task(_reply_predict(websocket, hour, line,
                                                                cluster_id, station_name, peer))
                        elif ctype == "incident_log":
                            # 시연 모드 / 운영자 콘솔이 사고 검출 시 송신
                            ev_type = ctrl.get("ev_type") or "unknown"
                            if ev_type in incident_state:
                                incident_state[ev_type] += 1
                            event = {
                                "ts": time.time(),
                                "type": ev_type,
                                "severity": ctrl.get("severity") or "med",
                                "msg": ctrl.get("msg") or "",
                                "source": ctrl.get("source") or "?",
                            }
                            incident_state["events"].insert(0, event)
                            if len(incident_state["events"]) > INCIDENT_KEEP:
                                incident_state["events"] = incident_state["events"][:INCIDENT_KEEP]
                            summary = {
                                "type": "incident_summary",
                                "emergency": incident_state["emergency"],
                                "suspicious": incident_state["suspicious"],
                                "lost": incident_state["lost"],
                                "free_ride": incident_state["free_ride"],
                                "priority_seat": incident_state["priority_seat"],
                                "bottleneck": incident_state["bottleneck"],
                                "events": incident_state["events"][:8],
                            }
                            asyncio.create_task(broadcast(json.dumps(summary, ensure_ascii=False)))
                    except Exception as e:
                        print(f"[ctrl] {peer} parse fail: {e}", flush=True)
                    continue
                if not isinstance(msg, (bytes, bytearray)):
                    continue
                rx["n"] += 1
                # 단일 active source 정책
                _now = time.time()
                if active_source["claimed"]:
                    # 명시 claim 모드 — claimed client만 처리, 다른 source는 무시
                    if active_source["ws"] is not websocket:
                        continue
                else:
                    # 자동 모드 — 가장 최근 송신자 우선 + 5초 TTL
                    if active_source["ws"] is None or _now > active_source["until"]:
                        if active_source["ws"] is not websocket:
                            print(f"[src] active → {peer}", flush=True)
                        active_source["ws"] = websocket
                        active_source["until"] = _now + ACTIVE_SOURCE_TTL
                    elif active_source["ws"] is not websocket:
                        continue
                    else:
                        active_source["until"] = _now + ACTIVE_SOURCE_TTL
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
            if active_source["ws"] is websocket:
                active_source["ws"] = None
                active_source["until"] = 0.0
                active_source["claimed"] = False
            print(f"[ws] 끊김 {peer} (남은 {len(clients)})", flush=True)

    # HTTP / 요청 (브라우저 직접 접속) → GitHub Pages 리다이렉트
    # WebSocket upgrade 요청은 Upgrade 헤더 있으니 통과시켜야 함 (publisher 등 WS client 영향 금지)
    try:
        from websockets.http11 import Response as _WSResponse
        from websockets.datastructures import Headers as _WSHeaders
        async def _process_request(connection, request):
            upgrade = (request.headers.get("Upgrade") or "").lower()
            if upgrade == "websocket":
                return None  # WS handshake 진행
            path = request.path.split("?")[0]
            if path == "/" or path == "":
                return _WSResponse(
                    301, "Moved Permanently",
                    _WSHeaders([("Location", "https://leelang7.github.io/MetroEyes/")]),
                    b"",
                )
            return None
    except Exception:
        _process_request = None

    print(f"[i] BEV multi-class (YOLO {args.model}) ws://0.0.0.0:{args.port}", flush=True)
    async with serve(handler, "0.0.0.0", args.port,
                     max_size=10 * 1024 * 1024,
                     process_request=_process_request):
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
