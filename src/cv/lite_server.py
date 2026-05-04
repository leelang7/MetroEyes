"""Lite WebSocket server — torch/ultralytics 없이 즉시 listen.

CV 검출은 안 함. 시민 PWA / 운영자 콘솔의 외부 API 라이브 호출만 처리:
  - arrival_query     : 서울 TOPIS 실시간 도착정보
  - population_query  : citydata_ppltn (성수동 등 110 POI 분 단위 인구)
  - citydata_query    : 통합 도시데이터 (날씨/공기/도로/따릉이/주차)
  - events_query      : 주변 문화 행사
  - impact_log        : 시민 임팩트 누적 + broadcast
  - 폭증 감지 → 네이버 뉴스 + Claude 요약 자동 broadcast

실행:
  python -m src.cv.lite_server --port 8765
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# pythonw 환경에서 stdout None 자동 redirect
if sys.stdout is None:
    _root = Path(__file__).resolve().parents[2]
    _log = _root / "logs"
    _log.mkdir(exist_ok=True)
    log_path = _log / f"lite_server_{os.getpid()}.log"
    sys.stdout = open(log_path, "a", encoding="utf-8", buffering=1)
    sys.stderr = sys.stdout

# .env 자동 로드
def _load_env():
    p = Path(__file__).resolve().parents[2] / ".env"
    if not p.exists(): return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1)
        if k and v and k not in os.environ:
            os.environ[k] = v.strip()
_load_env()

# websockets 만 외부 의존성 (간소함)
try:
    import websockets
except ImportError:
    print("[err] websockets 미설치. pip install websockets", flush=True)
    sys.exit(1)


SEOUL_KEY = os.environ.get("SEOUL_OPENDATA_API_KEY", "")
SUBWAY_KEY = os.environ.get("SEOUL_SUBWAY_ARRIVAL_KEY", "")
NAVER_ID = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

clients: set = set()
ppltn_history: dict[str, list] = {}        # poi → [(ts, mid)]
context_cache: dict[str, tuple] = {}       # poi → (ts, payload)
CONTEXT_TTL = 600.0


# ============== HTTP helpers ==============

def http_get(url: str, headers: dict | None = None, timeout: float = 5.0) -> dict:
    """동기 HTTP GET → JSON. 실패 시 {'_error': ...}."""
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read().decode("utf-8")
            return json.loads(data)
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}


def http_post_json(url: str, body: dict, headers: dict, timeout: float = 8.0) -> dict:
    try:
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"), headers=headers
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}


# ============== Seoul Open API fetchers ==============

def predict_surge(poi: str, hours_ahead: int = 24) -> dict:
    """24시간 폭증 예측 — 시간대 baseline + 과거 추세 + 행사 신호.

    단순 모델:
      base[h] = 출퇴근 양봉 + 시간대 가우시안
      hist_trend = ppltn_history 의 최근 1시간 ratio
      forecast[h+i] = base[h+i] × hist_trend × event_boost
      surge_prob[h+i] = sigmoid((forecast - threshold) × 5)
    """
    import math, time
    now = time.time()
    cur_hour = int(time.localtime().tm_hour)
    hist = ppltn_history.get(poi, [])
    hist_trend = 1.0
    if len(hist) >= 2:
        recent = sum(v for _, v in hist[-3:]) / max(1, len(hist[-3:]))
        early = sum(v for _, v in hist[:3]) / max(1, len(hist[:3]))
        if early > 0: hist_trend = recent / early
    # 시간대 baseline (출퇴근 양봉)
    def base(h):
        am = 0.7 * math.exp(-((h - 8) ** 2) / 4.0)
        pm = 0.85 * math.exp(-((h - 18) ** 2) / 5.0)
        leisure = 0.5 * math.exp(-((h - 20) ** 2) / 8.0)  # 성수/홍대 같은 핫스팟 저녁
        return 0.2 + am + pm + leisure
    # POI hot 가중치
    is_hot = any(k in poi for k in ["성수", "홍대", "서울숲", "뚝섬", "강남"])
    forecasts = []
    for i in range(hours_ahead):
        h = (cur_hour + i) % 24
        b = base(h)
        if is_hot: b *= 1.3
        f = b * hist_trend
        # surge_prob
        prob = 1.0 / (1.0 + math.exp(-(f - 1.5) * 3.0))
        forecasts.append({"hour": h, "level": round(f, 2), "surge_prob": round(prob, 2)})
    # peak hours (prob > 0.5) — 폭증 가능
    high_peaks = sorted([f for f in forecasts if f["surge_prob"] > 0.5], key=lambda x: -x["surge_prob"])[:3]
    # peak 없으면 상위 3개 (그냥 시간대별 강한 시간)
    peaks = high_peaks if high_peaks else sorted(forecasts, key=lambda x: -x["surge_prob"])[:3]
    if high_peaks:
        summary = f"{poi} 향후 {hours_ahead}h: 폭증 가능 {len(high_peaks)}개 — 가장 강 {peaks[0]['hour']}시 prob {peaks[0]['surge_prob']:.0%}"
    else:
        summary = f"{poi} 향후 {hours_ahead}h: 정상 — 가장 붐비는 시간 {peaks[0]['hour']}시"
    return {
        "type": "surge_forecast",
        "poi": poi,
        "fetched_at": now,
        "hist_trend": round(hist_trend, 2),
        "is_hot": is_hot,
        "forecasts": forecasts,
        "peaks": peaks,
        "summary": summary,
    }


async def fetch_population(poi: str) -> dict:
    """citydata_ppltn — 분 단위 POI 인구."""
    if not SEOUL_KEY:
        return {"type": "population", "poi": poi, "error": "SEOUL_OPENDATA_API_KEY 미설정"}
    url = f"http://openapi.seoul.go.kr:8088/{SEOUL_KEY}/json/citydata_ppltn/1/5/{urllib.parse.quote(poi)}"
    raw = await asyncio.get_event_loop().run_in_executor(None, http_get, url)
    val = raw.get("SeoulRtd.citydata_ppltn") if isinstance(raw, dict) else None
    if isinstance(val, list):
        rows = val
    elif isinstance(val, dict):
        rows = val.get("row") or []
    else:
        rows = []
    row = rows[0] if rows else {}
    payload = {
        "type": "population",
        "poi": poi,
        "fetched_at": time.time(),
        "area_nm": row.get("AREA_NM"),
        "congest_lvl": row.get("AREA_CONGEST_LVL"),
        "congest_msg": row.get("AREA_CONGEST_MSG"),
        "ppltn_min": _to_int(row.get("AREA_PPLTN_MIN")),
        "ppltn_max": _to_int(row.get("AREA_PPLTN_MAX")),
        "ppltn_time": row.get("PPLTN_TIME"),
        "error": raw.get("_error"),
    }
    # 폭증 감지 → 컨텍스트 자동 broadcast
    asyncio.create_task(_check_surge_and_broadcast(poi, payload))
    return payload


async def fetch_arrival(station: str, line: int | None) -> dict:
    """TOPIS 실시간 도착정보."""
    if not SUBWAY_KEY:
        return {"type": "arrival", "station": station, "items": [], "simulated": True,
                "error": "SEOUL_SUBWAY_ARRIVAL_KEY 미설정"}
    url = f"http://swopenapi.seoul.go.kr/api/subway/{SUBWAY_KEY}/json/realtimeStationArrival/0/8/{urllib.parse.quote(station)}"
    raw = await asyncio.get_event_loop().run_in_executor(None, http_get, url)
    items = []
    arr = raw.get("realtimeArrivalList") if isinstance(raw, dict) else None
    if isinstance(arr, list):
        for r in arr:
            if line and str(r.get("subwayId", ""))[-1:] != str(line):
                continue
            items.append({
                "subwayId": r.get("subwayId"),
                "trainLineNm": r.get("trainLineNm"),
                "bstatnNm": r.get("bstatnNm"),
                "arvlMsg2": r.get("arvlMsg2"),
                "arvlMsg3": r.get("arvlMsg3"),
                "arvlCd": r.get("arvlCd"),
                "barvlDt": _to_int(r.get("barvlDt")),
                "updnLine": r.get("updnLine"),
            })
    return {
        "type": "arrival", "station": station, "line": line,
        "items": items[:6], "fetched_at": time.time(),
        "error": raw.get("_error"),
        "simulated": not items and not raw.get("_error"),
    }


# ============== 인파 폭증 → 네이버 + LLM 컨텍스트 ==============

async def _check_surge_and_broadcast(poi: str, ppltn_payload: dict):
    """폭증 감지 시 fetch_context_news → broadcast."""
    mid = ((ppltn_payload.get("ppltn_min") or 0) + (ppltn_payload.get("ppltn_max") or 0)) / 2
    if mid <= 0:
        return
    hist = ppltn_history.setdefault(poi, [])
    hist.append((time.time(), mid))
    if len(hist) > 12: hist.pop(0)

    lvl = ppltn_payload.get("congest_lvl") or ""
    surge = lvl == "붐빔"
    if not surge and lvl == "약간 붐빔" and len(hist) >= 2:
        prev = hist[-2][1]
        surge = prev > 0 and (mid - prev) / prev > 0.05
    if not surge:
        return
    ctx = await fetch_context_news(poi)
    ctx["trigger"] = {"poi": poi, "lvl": lvl, "ppltn": int(mid)}
    await broadcast(json.dumps(ctx, ensure_ascii=False))


async def fetch_context_news(poi: str) -> dict:
    """네이버 뉴스 5건 + Claude 요약."""
    cached = context_cache.get(poi)
    if cached and time.time() - cached[0] < CONTEXT_TTL:
        return cached[1]
    loop = asyncio.get_event_loop()
    news = await loop.run_in_executor(None, _naver_news, poi)
    summary = await loop.run_in_executor(None, _claude_summarize, news, poi)
    payload = {
        "type": "context", "poi": poi, "fetched_at": time.time(),
        "summary": summary, "news": news,
        "sources": {
            "naver": bool(news) and bool(NAVER_ID),
            "llm": bool(ANTHROPIC_KEY) and bool(news),
        },
    }
    context_cache[poi] = (time.time(), payload)
    return payload


def _naver_news(poi: str) -> list:
    if not NAVER_ID or not NAVER_SECRET:
        return []
    short = poi
    if "성수" in poi: short = "성수동"
    elif "서울숲" in poi: short = "서울숲"
    elif "뚝섬" in poi: short = "뚝섬"
    elif "홍대" in poi: short = "홍대"
    q = f"{short} 인파"
    url = "https://openapi.naver.com/v1/search/news.json?" + urllib.parse.urlencode({
        "query": q, "display": 5, "sort": "date",
    })
    raw = http_get(url, headers={
        "X-Naver-Client-Id": NAVER_ID,
        "X-Naver-Client-Secret": NAVER_SECRET,
    }, timeout=4)
    if raw.get("_error"):
        return []
    items = []
    for it in raw.get("items", [])[:5]:
        title = re.sub(r"<[^>]+>", "", it.get("title", "")).replace("&quot;", '"').replace("&amp;", "&")
        desc = re.sub(r"<[^>]+>", "", it.get("description", ""))[:100]
        items.append({
            "title": title, "desc": desc,
            "link": it.get("link", ""), "pubDate": it.get("pubDate", ""),
        })
    return items


def _claude_summarize(news_items: list, poi: str) -> str:
    if not ANTHROPIC_KEY or not news_items:
        return news_items[0]["title"][:60] if news_items else f"{poi} 인파 폭증 — 행사·날씨·환승 영향"
    titles = "\n".join(f"- {it['title']}" for it in news_items[:5])
    body = {
        "model": "claude-haiku-4-5",
        "max_tokens": 80,
        "messages": [{"role": "user", "content":
            f"{poi} 지역 인파가 폭증했습니다. 다음 뉴스 5건을 보고 '왜 붐비는지' 한 줄(40자 이내)로 답하세요:\n{titles}"}],
    }
    resp = http_post_json("https://api.anthropic.com/v1/messages", body, {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }, timeout=8)
    if resp.get("_error"):
        return news_items[0]["title"][:60]
    txt = (resp.get("content") or [{}])[0].get("text", "").strip()
    return txt[:80] if txt else news_items[0]["title"][:60]


# ============== utils ==============

def _to_int(v):
    try: return int(v)
    except: return None


async def broadcast(text: str):
    if not clients: return
    stale = []
    for ws in clients:
        try:
            await asyncio.wait_for(ws.send(text), timeout=2)
        except Exception:
            stale.append(ws)
    for s in stale:
        clients.discard(s)


# ============== WebSocket handler ==============

async def handler(websocket):
    clients.add(websocket)
    print(f"[ws] connect {websocket.remote_address}, clients={len(clients)}", flush=True)
    try:
        async for msg in websocket:
            try:
                req = json.loads(msg)
            except Exception:
                continue
            t = req.get("type")
            if t == "population_query" and req.get("poi"):
                payload = await fetch_population(req["poi"])
                await websocket.send(json.dumps(payload, ensure_ascii=False))
            elif t == "citydata_query" and req.get("poi"):
                # 통합 — 일단 인구만 반환 (fallback). 정식은 fetch_citydata 추가 필요
                payload = await fetch_population(req["poi"])
                payload["type"] = "citydata"
                await websocket.send(json.dumps(payload, ensure_ascii=False))
            elif t == "arrival_query" and req.get("stationName"):
                payload = await fetch_arrival(req["stationName"], req.get("line"))
                await websocket.send(json.dumps(payload, ensure_ascii=False))
            elif t == "events_query":
                # 행사는 lite 에선 빈 응답
                await websocket.send(json.dumps({
                    "type": "events", "poi": req.get("poi"),
                    "events": [], "total_count": 0, "total_capacity": 0,
                }, ensure_ascii=False))
            elif t == "impact_log":
                pass
            elif t == "predict_surge" and req.get("poi"):
                # IDEA-7 24h 폭증 예측 — 과거 추세(ppltn_history) + 시간대 baseline + 행사 신호
                payload = predict_surge(req["poi"], req.get("hours_ahead", 24))
                await websocket.send(json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        print(f"[ws] err {e}", flush=True)
    finally:
        clients.discard(websocket)
        print(f"[ws] disconnect, clients={len(clients)}", flush=True)


async def http_health(path, headers):
    """GET / 같은 일반 HTTP 요청 처리 (curl 헬스체크)."""
    if path == "/health" or path == "/":
        return (200, [("content-type", "application/json")],
                json.dumps({
                    "ok": True, "mode": "lite",
                    "keys": {
                        "seoul": bool(SEOUL_KEY), "subway": bool(SUBWAY_KEY),
                        "naver": bool(NAVER_ID), "anthropic": bool(ANTHROPIC_KEY),
                    },
                    "clients": len(clients),
                }).encode("utf-8"))
    return None


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    print(f"[lite_server] starting on {args.host}:{args.port}", flush=True)
    print(f"  SEOUL={'ok' if SEOUL_KEY else 'MISSING'}  "
          f"SUBWAY={'ok' if SUBWAY_KEY else 'MISSING'}  "
          f"NAVER={'ok' if NAVER_ID else 'MISSING'}  "
          f"ANTHROPIC={'ok' if ANTHROPIC_KEY else 'MISSING'}", flush=True)

    async with websockets.serve(
        handler, args.host, args.port,
        process_request=http_health,
    ):
        print(f"[lite_server] LISTEN ws://{args.host}:{args.port}", flush=True)
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
