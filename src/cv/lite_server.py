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

# 누적 임팩트 — impact_log 들어오면 합산 후 impact_summary broadcast
_impact_total = {"count": 0, "saved_pct_sum": 0.0, "stations": {}, "krw_paid": 0,
                 "hourly": [0] * 24}  # 시간별 분산 액션 누적
IMPACT_AVG_TRIP_MIN = 25.0      # 평균 통행 시간 (분)
IMPACT_VALUE_PER_MIN = 167      # 혼잡 1분 당 사회적 비용 추정 (원) — 한국교통연구원 혼잡비용 환산
# 운영자 콘솔에 표시할 일평균 통행 (서울교통공사 2024) — 응답률 추정 기준
DAILY_RIDERS_BASELINE = 7_000_000

# 외부 API 호출 통계 — admin /health 가 폴링
_api_stats: dict[str, dict] = {}  # name → {calls, errors, last_ms, avg_ms, last_ts}

# CV 메트릭 — fake_bev_loop / 실 CV 둘 다 갱신
_cv_metrics: dict = {"fps": 0.0, "tracks": 0, "frames": 0, "last_ts": 0.0, "demo": False}

# 사고/이벤트 누적 — realbev/operator 가 incident_log 보내면 누적 + broadcast
_incident_total = {"emergency": 0, "suspicious": 0, "lost": 0, "free_ride": 0, "events": []}
INCIDENT_KEEP = 30  # 최근 30개만 유지

# 분당 메시지 통계 — 60분 deque
import collections
_msg_minute_buckets: collections.deque = collections.deque(maxlen=60)
_current_minute = {"ts": 0, "ws_msgs": 0, "api_calls": 0}

def _bump_msg_bucket(kind: str):
    """분당 ws/api 메시지 카운트 누적."""
    now = int(time.time() // 60)
    if _current_minute["ts"] != now:
        if _current_minute["ts"] != 0:
            _msg_minute_buckets.append(dict(_current_minute))
        _current_minute["ts"] = now
        _current_minute["ws_msgs"] = 0
        _current_minute["api_calls"] = 0
    if kind == "ws":
        _current_minute["ws_msgs"] += 1
    elif kind == "api":
        _current_minute["api_calls"] += 1

def _api_track(name: str, started: float, error: bool = False):
    """API 호출 시간 + 성공/실패 통계 누적."""
    elapsed_ms = (time.time() - started) * 1000.0
    s = _api_stats.setdefault(name, {"calls": 0, "errors": 0, "total_ms": 0.0, "last_ms": 0.0, "last_ts": 0.0})
    s["calls"] += 1
    if error: s["errors"] += 1
    s["total_ms"] += elapsed_ms
    s["last_ms"] = elapsed_ms
    s["last_ts"] = time.time()
    _bump_msg_bucket("api")


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
    _t0 = time.time()
    raw = await asyncio.get_event_loop().run_in_executor(None, http_get, url)
    _api_track("citydata_ppltn", _t0, error=bool(raw.get("_error")))
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
    _t0 = time.time()
    raw = await asyncio.get_event_loop().run_in_executor(None, http_get, url)
    _api_track("realtimeStationArrival", _t0, error=bool(raw.get("_error")))
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
    _t0 = time.time()
    news = await loop.run_in_executor(None, _naver_news, poi)
    _api_track("naver_news", _t0, error=not news)
    _t1 = time.time()
    summary = await loop.run_in_executor(None, _claude_summarize, news, poi)
    _api_track("claude_summary", _t1, error=not summary)
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

def _build_impact_summary() -> dict:
    """현재 누적 임팩트를 dict 로 — 신규 join + impact_log 시 공통 사용."""
    n = _impact_total["count"]
    avg_saved = _impact_total["saved_pct_sum"] / max(1, n) if n else 0.0
    saved_min_total = (_impact_total["saved_pct_sum"] / 100.0) * IMPACT_AVG_TRIP_MIN
    value_won = int(saved_min_total * IMPACT_VALUE_PER_MIN)
    top_st = max(_impact_total["stations"].items(), key=lambda x: x[1])[0] if _impact_total["stations"] else None
    est_response_rate = min(1.0, n * 1000 / DAILY_RIDERS_BASELINE) if n else 0.0
    policy_cost = _impact_total["krw_paid"] or 1
    roi_x = value_won / policy_cost if policy_cost else 0
    # 시간대별 분산 액션 분포 (24h)
    hourly = _impact_total.get("hourly", [0] * 24)
    return {
        "type": "impact_summary",
        "total_count": n,
        "avg_saved_pct": round(avg_saved, 1),
        "saved_min_total": round(saved_min_total, 1),
        "value_won": value_won,
        "top_station": top_st,
        "krw_paid": _impact_total["krw_paid"],
        "est_response_rate": round(est_response_rate, 4),
        "roi_x": round(roi_x, 1),
        "hourly": hourly,
        "stations": dict(sorted(_impact_total["stations"].items(), key=lambda x: -x[1])[:8]),
    }


async def handler(websocket):
    clients.add(websocket)
    print(f"[ws] connect {websocket.remote_address}, clients={len(clients)}", flush=True)
    # 신규 클라이언트 join 시 즉시 현재 누적 impact_summary 전송 (페이지 reload 후에도 카운터 유지)
    try:
        if _impact_total["count"] > 0:
            await websocket.send(json.dumps(_build_impact_summary(), ensure_ascii=False))
    except Exception:
        pass
    try:
        async for msg in websocket:
            _bump_msg_bucket("ws")
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
                saved = float(req.get("saved_pct") or 0)
                krw = int(req.get("krw") or 0)
                _impact_total["count"] += 1
                _impact_total["saved_pct_sum"] += saved
                _impact_total["krw_paid"] += krw
                st = req.get("station") or "?"
                _impact_total["stations"][st] = _impact_total["stations"].get(st, 0) + 1
                _impact_total["hourly"][time.localtime().tm_hour] += 1
                await broadcast(json.dumps(_build_impact_summary(), ensure_ascii=False))
            elif t == "incident_log":
                # realbev / operator 가 응급·분실·이상·무임 검출 시 송신
                ev_type = req.get("ev_type") or "unknown"
                if ev_type in _incident_total:
                    _incident_total[ev_type] += 1
                event = {
                    "ts": time.time(),
                    "type": ev_type,
                    "severity": req.get("severity") or "med",
                    "msg": req.get("msg") or "",
                    "source": req.get("source") or "?",  # realbev / operator-subway / operator-bus
                }
                _incident_total["events"].insert(0, event)
                if len(_incident_total["events"]) > INCIDENT_KEEP:
                    _incident_total["events"] = _incident_total["events"][:INCIDENT_KEEP]
                summary = {
                    "type": "incident_summary",
                    "emergency": _incident_total["emergency"],
                    "suspicious": _incident_total["suspicious"],
                    "lost": _incident_total["lost"],
                    "free_ride": _incident_total["free_ride"],
                    "events": _incident_total["events"][:8],
                }
                await broadcast(json.dumps(summary, ensure_ascii=False))
            elif t == "predict_surge" and req.get("poi"):
                # IDEA-7 24h 폭증 예측 — 과거 추세(ppltn_history) + 시간대 baseline + 행사 신호
                payload = predict_surge(req["poi"], req.get("hours_ahead", 24))
                await websocket.send(json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        print(f"[ws] err {e}", flush=True)
    finally:
        clients.discard(websocket)
        print(f"[ws] disconnect, clients={len(clients)}", flush=True)


async def fake_impact_seed_loop():
    """--demo 모드 — 시뮬 시민 분산 액션 자동 누적.

    양봉 시간 (8/18) 가중치로 자동 impact_log 생성 → 첫 진입 시 KPI/sparkline 즉시 표시.
    1분당 평균 3건 (피크 8건, 야간 1건) 시뮬 발생.
    """
    import random
    rng = random.Random(7)
    STATIONS = [
        "성수카페거리", "강남역", "홍대 관광특구",  # hot
        "잠실역", "서울숲", "건대입구역", "서울역",  # medium
        "신촌·이대역", "광화문·덕수궁", "여의도", "남산공원", "뚝섬한강공원",  # low
    ]
    STATION_WEIGHTS = [3.5, 3.0, 2.8, 1.8, 1.5, 1.2, 1.5, 1.0, 1.0, 0.8, 0.6, 0.7]
    # Warm seed — 시작 즉시 12건 누적 + hourly 분포 양봉 형태 (지난 24h 시뮬)
    for _ in range(12):
        sv = rng.choices([7, 12, 22, 35, 5], weights=[0.25, 0.30, 0.25, 0.10, 0.10])[0]
        krw = 200 if sv >= 30 else 150 if sv >= 15 else 100 if sv >= 5 else 0
        st = rng.choices(STATIONS, weights=STATION_WEIGHTS)[0]
        h_seed = rng.choices(list(range(24)),
                             weights=[0.5, 0.3, 0.2, 0.2, 0.3, 0.8, 1.5, 4.0, 7.0, 4.5, 2.5, 2.0,
                                      2.5, 2.5, 2.5, 2.5, 3.0, 5.0, 7.0, 4.5, 2.5, 2.0, 1.0, 0.6])[0]
        _impact_total["count"] += 1
        _impact_total["saved_pct_sum"] += sv
        _impact_total["krw_paid"] += krw
        _impact_total["stations"][st] = _impact_total["stations"].get(st, 0) + 1
        _impact_total["hourly"][h_seed] += 1
    print(f"[seed] 12 warm impact seeds 즉시 누적 — 첫 진입 KPI 라이브", flush=True)
    while True:
        # 양봉 가중치 계산
        h = time.localtime().tm_hour
        if h in (7, 8, 9, 17, 18, 19): rate = 8.0      # 피크
        elif h in (10, 11, 12, 13, 14, 15, 16, 20, 21, 22): rate = 3.0  # 보통
        elif h in (5, 6, 23): rate = 1.5
        else: rate = 0.4   # 새벽
        # 1분당 rate 건 → 60초 / rate 간격
        interval = max(8, 60.0 / rate)
        await asyncio.sleep(interval + rng.uniform(-2, 2))
        # 분산률 차등
        sv = rng.choices([7, 12, 22, 35, 5], weights=[0.25, 0.30, 0.25, 0.10, 0.10])[0]
        krw = 200 if sv >= 30 else 150 if sv >= 15 else 100 if sv >= 5 else 0
        st = rng.choices(STATIONS, weights=STATION_WEIGHTS)[0]
        # 누적
        _impact_total["count"] += 1
        _impact_total["saved_pct_sum"] += sv
        _impact_total["krw_paid"] += krw
        _impact_total["stations"][st] = _impact_total["stations"].get(st, 0) + 1
        _impact_total["hourly"][h] += 1
        # broadcast (클라이언트 있을 때만)
        if clients:
            try:
                await broadcast(json.dumps(_build_impact_summary(), ensure_ascii=False))
            except Exception: pass


async def fake_incident_seed_loop():
    """--demo 모드 — 5분마다 무작위 incident 1건 자동 발생.

    시연 중 끊임없이 사고가 발생하는 라이브 환경 시뮬.
    """
    import random
    rng = random.Random(13)
    TYPES = [
        ("free_ride", "med", "무임 의심 — 카드 미스캔", 0.30),
        ("lost", "low", "분실 가방 — BoT-SORT 12초+ 무인", 0.25),
        ("emergency", "high", "응급 — 30초+ 정지 + AED 거리", 0.10),
        ("suspicious", "high", "이상행동 — 환승 통로 군집", 0.15),
        ("free_ride", "med", "자동 분산 안내 송출 — 만석", 0.20),
    ]
    while True:
        await asyncio.sleep(300 + rng.uniform(-60, 60))   # 5분 ± 1분
        ev_type, sev, msg, _ = rng.choice(TYPES)
        if ev_type in _incident_total:
            _incident_total[ev_type] += 1
        event = {
            "ts": time.time(),
            "type": ev_type, "severity": sev,
            "msg": msg + " (자동 시뮬)",
            "source": "demo-auto",
        }
        _incident_total["events"].insert(0, event)
        if len(_incident_total["events"]) > INCIDENT_KEEP:
            _incident_total["events"] = _incident_total["events"][:INCIDENT_KEEP]
        if clients:
            try:
                summary = {
                    "type": "incident_summary",
                    "emergency": _incident_total["emergency"],
                    "suspicious": _incident_total["suspicious"],
                    "lost": _incident_total["lost"],
                    "free_ride": _incident_total["free_ride"],
                    "events": _incident_total["events"][:8],
                }
                await broadcast(json.dumps(summary, ensure_ascii=False))
            except Exception: pass


async def fake_bev_loop():
    """시연 fail-safe — 자체 CV 모델 부재 시에도 BEV tracks broadcast.

    사인파 + 시간대별 점유 변동으로 그럴듯한 트랙 7~25개 생성.
    운영자 콘솔의 'LIVE · N fps · M 트랙' 라벨이 살아있도록 5 Hz 송출.
    """
    import math
    import random
    t0 = time.time()
    fps_cnt = 0
    fps_t = t0
    fps_val = 5.0
    rng = random.Random(42)
    while True:
        await asyncio.sleep(0.2)
        fps_cnt += 1
        now = time.time()
        if now - fps_t >= 1.0:
            fps_val = fps_cnt / (now - fps_t)
            fps_cnt = 0; fps_t = now
        if not clients:
            continue
        # 시간대별 점유 (0.3~1.2 multiplier — 출퇴근 양봉 모방)
        h = time.localtime(now).tm_hour
        peak_factor = 1.0
        if 7 <= h <= 9 or 17 <= h <= 19:
            peak_factor = 1.2
        elif 23 <= h or h <= 5:
            peak_factor = 0.35
        n_tracks = max(3, int(rng.gauss(15 * peak_factor, 3)))
        tracks = []
        phase = (now - t0) * 0.5
        for i in range(n_tracks):
            # 칸별 분포 (10량 × 호차 기준 BEV)
            car_idx = i % 10
            bev_x = (car_idx + 0.5) * 32 + rng.gauss(0, 8) + math.sin(phase + i * 0.7) * 5
            bev_y = 16 + rng.gauss(0, 4) + math.cos(phase + i * 0.5) * 3
            tracks.append({
                "id": i + 1,
                "bev_x": round(max(0, min(320, bev_x)), 1),
                "bev_y": round(max(0, min(32, bev_y)), 1),
                "cls": "person",
                "conf": round(0.7 + rng.random() * 0.25, 2),
            })
        # 가끔 가방 (분실 검출 데모)
        if int(now) % 30 < 6:
            tracks.append({"id": 99, "bev_x": 96.0, "bev_y": 26.0, "cls": "backpack", "conf": 0.83})
        payload = {
            "type": "bev",
            "ts": now,
            "fps": round(fps_val, 1),
            "tracks": tracks,
            "demo": True,
        }
        # CV 메트릭 갱신
        _cv_metrics["fps"] = round(fps_val, 1)
        _cv_metrics["tracks"] = len(tracks)
        _cv_metrics["frames"] += 1
        _cv_metrics["last_ts"] = now
        _cv_metrics["demo"] = True
        await broadcast(json.dumps(payload, ensure_ascii=False))


CORS_HEADERS = [
    ("access-control-allow-origin", "*"),
    ("access-control-allow-methods", "GET, OPTIONS"),
    ("access-control-allow-headers", "*"),
    ("access-control-max-age", "86400"),
]


def _simulate_roi_curve(samples: int = 81) -> list:
    """ROI v3 closed-form curve — 0~80% 응답률 N 샘플."""
    KRW_HOUR = 15000
    out = []
    for i in range(samples):
        r = (i / max(1, samples - 1)) * 0.80
        min_saved = 1577 * r  # M분 — pitch.html simulateROI 동일 보간
        commute = (min_saved * 1e6 / 60) * KRW_HOUR / 1e8
        safety = 500 * (0.4 + r * 0.6) * 1.3
        ad = 120 * (0.5 + r * 0.7)
        energy = 150 * r * 1.3
        incentive = 7e6 * 250 * r * 0.45 * 100 / 1e8
        total = commute + safety + ad + energy
        net = total - incentive
        infra = 134 * 3_000_000 / 1e8
        roi = net / infra if infra > 0 else 0
        out.append({
            "rate": round(r, 4),
            "min_saved_m": round(min_saved, 1),
            "commute_b": round(commute, 1),
            "safety_b": round(safety, 1),
            "ad_b": round(ad, 1),
            "energy_b": round(energy, 1),
            "incentive_b": round(incentive, 1),
            "net_b": round(net, 1),
            "roi_x": round(roi, 1),
        })
    return out


async def http_health(path, headers):
    """GET / 같은 일반 HTTP 요청 처리 (curl 헬스체크) + API 호출 통계 + CORS + ROI 곡선."""
    # OPTIONS preflight (브라우저 fetch CORS)
    if hasattr(headers, "get") and headers.get("access-control-request-method"):
        return (204, CORS_HEADERS, b"")
    if path == "/api/v1/impact":
        # /api/v1/impact — 누적 임팩트 JSON
        body = json.dumps({
            "ok": True,
            "summary": _build_impact_summary() if _impact_total["count"] > 0 else None,
            "raw": {
                "count": _impact_total["count"],
                "krw_paid": _impact_total["krw_paid"],
                "saved_pct_sum": _impact_total["saved_pct_sum"],
                "stations": dict(_impact_total["stations"]),
                "hourly": list(_impact_total["hourly"]),
            },
        }).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    if path == "/api/docs":
        body = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<title>MetroEyes API</title>"
            "<style>body{font-family:'Noto Sans KR',sans-serif;max-width:760px;margin:30px auto;padding:0 20px;background:#0a0a0e;color:#e8e8ee;line-height:1.6}"
            "h1{color:#7dd3d3}h2{color:#10b981;border-bottom:1px solid rgba(125,211,211,.18);padding-bottom:6px;margin-top:28px}"
            "code{background:#14141a;padding:2px 8px;border-radius:4px;color:#f59e0b;font-size:13px}"
            "pre{background:#14141a;padding:14px;border-radius:8px;overflow:auto}"
            "table{border-collapse:collapse;width:100%}td,th{padding:6px 10px;border-bottom:1px solid #2a2a36;text-align:left}"
            "</style></head><body>"
            "<h1>MetroEyes API v1</h1>"
            "<p>모든 endpoint CORS 허용 (<code>Access-Control-Allow-Origin: *</code>) · GET only</p>"
            "<h2>GET <code>/health</code></h2>"
            "<p>전체 시스템 상태 (keys / clients / impact / api / cv / incidents / msg_per_min)</p>"
            "<h2>GET <code>/api/v1/roi_curve</code></h2>"
            "<p>ROI v3 closed-form 시뮬 — 81 샘플 (응답률 0~80%)</p>"
            "<pre>fetch('/api/v1/roi_curve').then(r=&gt;r.json()).then(j=&gt;j.curve)</pre>"
            "<h2>GET <code>/api/v1/impact</code></h2>"
            "<p>실시간 누적 임팩트 (분산 액션 / krw / 시간대 / 역별)</p>"
            "<h2>WebSocket <code>ws://host:8765</code></h2>"
            "<p>impact_log / incident_log / arrival_query / population_query / predict_surge 등</p>"
            "<table><tr><th>Type</th><th>Args</th><th>응답</th></tr>"
            "<tr><td>population_query</td><td>poi</td><td>{type:'population', congest_lvl, ppltn}</td></tr>"
            "<tr><td>arrival_query</td><td>stationName, line</td><td>{type:'arrival', items}</td></tr>"
            "<tr><td>impact_log</td><td>station, car, saved_pct, krw</td><td>broadcast impact_summary</td></tr>"
            "<tr><td>incident_log</td><td>ev_type, severity, msg, source</td><td>broadcast incident_summary</td></tr>"
            "</table>"
            "<p style='margin-top:30px;color:#8a8a96;font-size:12px'>License: Apache 2.0 · 2026 Seoul Big Data</p>"
            "</body></html>"
        ).encode("utf-8")
        return (200, [("content-type", "text/html; charset=utf-8")] + CORS_HEADERS, body)
    if path == "/api/v1/roi_curve":
        body = json.dumps({
            "ok": True,
            "model": "ROI v3 closed-form",
            "samples": 81,
            "curve": _simulate_roi_curve(81),
            "interpretation": {
                "scenarios": {
                    "very_conservative_5pct": "응답 5% — ROI ~120x",
                    "conservative_15pct": "응답 15% — ROI ~211x",
                    "mid_30pct": "응답 30% — ROI ~347x (현실적 중간)",
                    "optimistic_50pct": "응답 50% — ROI ~528x",
                    "ideal_70pct": "응답 70% — ROI ~709x",
                },
            },
        }).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    if path == "/health" or path == "/":
        api = {}
        for name, s in _api_stats.items():
            api[name] = {
                "calls": s["calls"],
                "errors": s["errors"],
                "last_ms": round(s["last_ms"], 1),
                "avg_ms": round(s["total_ms"] / max(1, s["calls"]), 1),
                "last_ts": s["last_ts"],
                "error_rate": round(s["errors"] / max(1, s["calls"]), 3),
            }
        body = json.dumps({
            "ok": True, "mode": "lite",
            "keys": {
                "seoul": bool(SEOUL_KEY), "subway": bool(SUBWAY_KEY),
                "naver": bool(NAVER_ID), "anthropic": bool(ANTHROPIC_KEY),
            },
            "clients": len(clients),
            "impact": _build_impact_summary() if _impact_total["count"] > 0 else None,
            "api": api,
            "cv": _cv_metrics if _cv_metrics["frames"] > 0 else None,
            "incidents": {
                "emergency": _incident_total["emergency"],
                "suspicious": _incident_total["suspicious"],
                "lost": _incident_total["lost"],
                "free_ride": _incident_total["free_ride"],
                "recent": _incident_total["events"][:5],
            } if (_incident_total["emergency"] + _incident_total["suspicious"] + _incident_total["lost"] + _incident_total["free_ride"]) > 0 else None,
            "msg_per_min": list(_msg_minute_buckets) + [dict(_current_minute)] if _current_minute["ts"] else list(_msg_minute_buckets),
        }).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    return None


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--demo", action="store_true",
                        help="fake BEV tracks broadcast (CV 모델 없이도 시연 OK)")
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
        if args.demo:
            print("[lite_server] DEMO mode — fake BEV tracks broadcast @5Hz", flush=True)
            print("[lite_server] DEMO mode — fake impact seed (양봉 시뮬 분산 액션 자동 누적)", flush=True)
            # incident warm seed — 시작 즉시 4건 (다양한 type)
            _incident_total["emergency"] = 1
            _incident_total["lost"] = 2
            _incident_total["free_ride"] = 1
            now = time.time()
            _incident_total["events"] = [
                {"ts": now - 60, "type": "lost", "severity": "low", "msg": "분실 BoT-SORT — 4호차 가방 12초 무인", "source": "demo-seed"},
                {"ts": now - 240, "type": "emergency", "severity": "high", "msg": "응급 골든타임 — 7호차 30초+ 정지 (AED 28m)", "source": "demo-seed"},
                {"ts": now - 480, "type": "free_ride", "severity": "med", "msg": "무임 의심 — 6호차 태그 미스캔", "source": "demo-seed"},
                {"ts": now - 720, "type": "lost", "severity": "low", "msg": "분실 — 환승 통로 우산 무인", "source": "demo-seed"},
            ]
            print("[seed] 4 warm incident seeds (admin timeline 즉시 라이브)", flush=True)
            print("[lite_server] DEMO mode — fake_incident_seed_loop 5분마다 자동 사고", flush=True)
            asyncio.create_task(fake_bev_loop())
            asyncio.create_task(fake_impact_seed_loop())
            asyncio.create_task(fake_incident_seed_loop())
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
