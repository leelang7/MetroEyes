"""FastAPI 백엔드 — 운영자/승객 채널 + BEV 추론 결과 스트리밍.

기동:
    uvicorn src.api.main:app --reload --port 8000
"""
from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.utils.settings import load_config, load_env


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.cfg = load_config("default")
    app.state.env = load_env()
    yield


app = FastAPI(title="MetroEyes API", version="0.0.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "ts": time.time()}


@app.get("/api/cars/{train_id}")
async def car_status(train_id: str) -> dict:
    """편성(train_id) 단위로 칸별 점유 요약 — 더미 응답.

    추후 src.inference.engine 결과로 교체.
    """
    return {
        "train_id": train_id,
        "cars": [
            {"car_no": i, "occupancy": 0.0, "count": 0, "density": 0.0}
            for i in range(1, 11)
        ],
        "ts": time.time(),
    }


@app.websocket("/ws/bev")
async def ws_bev(ws: WebSocket) -> None:
    """BEV 점유 그리드 실시간 스트림 — 1Hz 더미 송출.

    후속: src.inference.engine 의 큐를 구독해 그대로 직렬화.
    """
    await ws.accept()
    try:
        while True:
            payload = {
                "ts": time.time(),
                "grid_shape": [195, 28],
                "occupancy_summary": 0.0,
            }
            await ws.send_text(json.dumps(payload))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        return
