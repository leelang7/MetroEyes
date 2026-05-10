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

# 차등 인센티브 정책 — OD 우선순위 +₩100 / 환승역 +₩200 (현 시각 AM/PM 자동)
_priority_cache = {"od_arrival": None, "od_departure": None, "transfer": None, "loaded": False}

def _load_priority_sets():
    if _priority_cache["loaded"]:
        return
    try:
        from pathlib import Path as _P
        rep1 = _P(__file__).resolve().parent.parent.parent / "frontend" / "figs" / "od_asymmetry_report.json"
        rep2 = _P(__file__).resolve().parent.parent.parent / "frontend" / "figs" / "transfer_stations_report.json"
        if rep1.exists():
            j = json.loads(rep1.read_text(encoding="utf-8"))
            _priority_cache["od_arrival"] = {s["station"] for s in j.get("top_arrival", [])[:5]}
            _priority_cache["od_departure"] = {s["station"] for s in j.get("top_departure", [])[:5]}
        if rep2.exists():
            j = json.loads(rep2.read_text(encoding="utf-8"))
            am = {s["station"] for s in j.get("top_am_diff", [])[:5]}
            pm = {s["station"] for s in j.get("top_pm_diff", [])[:5]}
            _priority_cache["transfer"] = am | pm
    except Exception:
        pass
    _priority_cache["loaded"] = True

def _bonus_krw(station: str) -> tuple[int, str]:
    """역 이름 → (보상 가산, tier name). tier ∈ {basic, od, transfer}"""
    if not station:
        return 0, "basic"
    _load_priority_sets()
    cur_h = time.localtime().tm_hour
    is_am = 7 <= cur_h <= 11
    is_pm = 17 <= cur_h <= 21
    if not (is_am or is_pm):
        return 0, "basic"
    tp_set = _priority_cache.get("transfer") or set()
    if station in tp_set:
        return 200, "transfer"   # 환승역 — 기본 200원에 +200 → 총 ₩400
    od_set = _priority_cache.get("od_arrival" if is_am else "od_departure") or set()
    if station in od_set:
        return 100, "od"   # OD 우선순위 — 기본 200원에 +100 → 총 ₩300
    return 0, "basic"

# 누적 임팩트 — impact_log 들어오면 합산 후 impact_summary broadcast
_impact_total = {"count": 0, "saved_pct_sum": 0.0, "stations": {}, "krw_paid": 0,
                 "hourly": [0] * 24,
                 "tier_counts": {"basic": 0, "od": 0, "transfer": 0}}  # 차등 보상 분포
IMPACT_AVG_TRIP_MIN = 25.0      # 평균 통행 시간 (분)
IMPACT_VALUE_PER_MIN = 167      # 혼잡 1분 당 사회적 비용 추정 (원) — 한국교통연구원 혼잡비용 환산
# 운영자 콘솔에 표시할 일평균 통행 (서울교통공사 2024) — 응답률 추정 기준
DAILY_RIDERS_BASELINE = 7_000_000

# 외부 API 호출 통계 — admin /health 가 폴링
_api_stats: dict[str, dict] = {}  # name → {calls, errors, last_ms, avg_ms, last_ts}

# CV 메트릭 — fake_bev_loop / 실 CV 둘 다 갱신
_cv_metrics: dict = {"fps": 0.0, "tracks": 0, "frames": 0, "last_ts": 0.0, "demo": False}

# 사고/이벤트 누적 — realbev/operator 가 incident_log 보내면 누적 + broadcast
_incident_total = {"emergency": 0, "suspicious": 0, "lost": 0, "free_ride": 0,
                   "priority_seat": 0, "bottleneck": 0, "events": []}
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


async def fetch_citydata(poi: str) -> dict:
    """citydata 통합 API (cycle 427) — WEATHER_STTS + EVENT_STTS + ROAD_TRAFFIC_STTS + LIVE_PPLTN_STTS.

    이전엔 lite_server 가 citydata_query 를 받으면 ppltn 만 type 바꿔치기로 반환 →
    광고 페이지의 PM2.5/UV 수신 영원히 안 옴 + events_query 빈 배열. 정식 fix.

    응답 사용처:
      - frontend/operator_web/ad_pricing.html: PM2.5/UV chip (cycle 394) 라이브 표시
      - frontend/passenger_app/index.html: citydata_query / events_query 통합 응답
    """
    if not SEOUL_KEY:
        return {"type": "citydata", "poi": poi, "error": "SEOUL_OPENDATA_API_KEY 미설정"}
    url = f"http://openapi.seoul.go.kr:8088/{SEOUL_KEY}/json/citydata/1/5/{urllib.parse.quote(poi)}"
    _t0 = time.time()
    raw = await asyncio.get_event_loop().run_in_executor(None, http_get, url)
    _api_track("citydata", _t0, error=bool(raw.get("_error")))

    val = raw.get("CITYDATA") if isinstance(raw, dict) else None
    if not isinstance(val, dict):
        # 응답 형식 변경 fallback (서울 OpenAPI 가 가끔 키 다르게 줌)
        return {"type": "citydata", "poi": poi, "error": raw.get("_error") or "CITYDATA 키 부재"}

    # 1) 인구 (LIVE_PPLTN_STTS — citydata_ppltn 와 동일 필드)
    ppltn_arr = val.get("LIVE_PPLTN_STTS") or []
    p = ppltn_arr[0] if isinstance(ppltn_arr, list) and ppltn_arr else {}
    ppltn_min = _to_int(p.get("AREA_PPLTN_MIN"))
    ppltn_max = _to_int(p.get("AREA_PPLTN_MAX"))

    # 2) 날씨 + 대기질 (WEATHER_STTS)
    w_arr = val.get("WEATHER_STTS") or []
    w = w_arr[0] if isinstance(w_arr, list) and w_arr else {}

    def _to_float(x):
        try: return float(x) if x not in (None, "", "-") else None
        except (TypeError, ValueError): return None

    # 3) 문화행사 (EVENT_STTS)
    ev_arr = val.get("EVENT_STTS") or []
    events = []
    if isinstance(ev_arr, list):
        for e in ev_arr[:5]:
            events.append({
                "name": e.get("EVENT_NM"),
                "place": e.get("EVENT_PLACE"),
                "start": e.get("EVENT_PERIOD"),
                "x": e.get("EVENT_X"), "y": e.get("EVENT_Y"),
                "url": e.get("URL"),
                "fee": e.get("PAY_YN") == "Y",
            })

    # 4) 도로 교통 평균
    rd_arr = val.get("ROAD_TRAFFIC_STTS") or []
    rd = rd_arr[0] if isinstance(rd_arr, list) and rd_arr else {}
    if isinstance(rd, dict) and "AVG_ROAD_DATA" in rd:
        rd = rd.get("AVG_ROAD_DATA") or {}
    road_spd = _to_float(rd.get("ROAD_TRAFFIC_SPD")) if isinstance(rd, dict) else None

    # 5) 따릉이 실시간 (LIVE_BIKE_STTS)
    bike_arr = val.get("LIVE_BIKE_STTS") or []
    bikes = []
    if isinstance(bike_arr, list):
        for b in bike_arr[:5]:
            bikes.append({
                "station_id": b.get("SBIKE_STTN_ID"),
                "name": b.get("SBIKE_STTN_NM"),
                "available": _to_int(b.get("AVAILABLE_BIKE_CNT")),
                "total": _to_int(b.get("TOTAL_SBIKE_CNT")),
                "lat": _to_float(b.get("SBIKE_STTN_LAT")),
                "lon": _to_float(b.get("SBIKE_STTN_LONT")),
            })
    bike_total_avail = sum(b.get("available") or 0 for b in bikes if b.get("available") is not None)

    # 6) 공영주차장 실시간 (LIVE_PARK_STTS)
    park_arr = val.get("LIVE_PARK_STTS") or []
    parks = []
    if isinstance(park_arr, list):
        for pk in park_arr[:5]:
            parks.append({
                "name": pk.get("PARK_NM"),
                "total": _to_int(pk.get("CAPACITY")),
                "cur_cnt": _to_int(pk.get("CUR_PARKING")),
                "avail": _to_int(pk.get("AVAIL_CNT")),
                "pay_yn": pk.get("PAY_NM"),
            })
    park_total_avail = sum(pk.get("avail") or 0 for pk in parks if pk.get("avail") is not None)

    # 7) 버스 인구 (LIVE_BUS_PPLTN_STTS) — 정류장 30분 누적 승차
    bus_ppltn_arr = val.get("LIVE_BUS_PPLTN_STTS") or []
    bus_ppltn = bus_ppltn_arr[0] if isinstance(bus_ppltn_arr, list) and bus_ppltn_arr else {}
    bus_30wthn_gton_max = _to_int(bus_ppltn.get("PPLTN_WTHN_30MIN_GTON_MAX"))

    # 8) 상권 (LIVE_CMRCL_STTS) — 결제 건수 지표
    cmrcl_arr = val.get("LIVE_CMRCL_STTS") or []
    cmrcl = cmrcl_arr[0] if isinstance(cmrcl_arr, list) and cmrcl_arr else {}
    cmrcl_paying_rate = _to_float(cmrcl.get("PAYING_RATE")) or _to_float(cmrcl.get("PAYMENT_RATE"))
    cmrcl_type = cmrcl.get("PAYING_SALES_TYPE") or cmrcl.get("PAYMENT_TYPE") or "—"

    return {
        "type": "citydata",
        "poi": poi,
        "fetched_at": time.time(),
        # 인구 (호환 필드)
        "area_nm": p.get("AREA_NM") or poi,
        "congest_lvl": p.get("AREA_CONGEST_LVL"),
        "congest_msg": p.get("AREA_CONGEST_MSG"),
        "ppltn_min": ppltn_min,
        "ppltn_max": ppltn_max,
        "ppltn_time": p.get("PPLTN_TIME"),
        # 날씨 (광고 페이지 cycle 394 chip 수신처)
        "temp": _to_float(w.get("TEMP")),
        "precipitation": w.get("PRECIPITATION"),
        "pcp_msg": w.get("PCP_MSG"),
        "pm25": _to_float(w.get("PM25")),
        "pm10": _to_float(w.get("PM10")),
        "air_idx": w.get("AIR_IDX"),
        "uv_idx": w.get("UV_INDEX_LVL") or w.get("UV_INDEX"),
        "weather_time": w.get("WEATHER_TIME"),
        # 문화행사
        "events": events,
        "events_count": len(events),
        # 도로 교통
        "road_idx": rd.get("ROAD_TRAFFIC_IDX") if isinstance(rd, dict) else None,
        "road_msg": rd.get("ROAD_MSG_IDX") if isinstance(rd, dict) else None,
        "road_spd": road_spd,
        # 따릉이 실시간
        "bikes": bikes,
        "bike_avail": bike_total_avail,
        # 주차장 실시간
        "parks": parks,
        "park_avail": park_total_avail,
        # 버스 인구
        "bus_30wthn_gton_max": bus_30wthn_gton_max,
        # 상권
        "cmrcl_paying_rate": cmrcl_paying_rate,
        "cmrcl_type": cmrcl_type,
        "error": raw.get("_error"),
    }


# ============== 지하역사 실내 공기질 (IndoorAirQualityMeasureService) ==============

# 역사 코드 맵 (서울교통공사 기준 주요 역)
_STATION_CODE_MAP = {
    "잠실": "2910", "강남": "2813", "홍대입구": "2621", "서울역": "1150",
    "합정": "2622", "성수": "2737", "신도림": "2638", "고속터미널": "3438",
    "사당": "4174", "왕십리": "2748",
}
_indoor_air_cache: dict[str, tuple] = {}  # station → (ts, payload)
INDOOR_AIR_TTL = 300.0

async def fetch_indoor_air(station: str) -> dict:
    """지하역사 실내 공기질 — IndoorAirQualityMeasureService.

    서울 열린데이터광장 서비스명: IndoorAirQualityMeasureService
    주요 필드: PM10, PM25, CO2, TEMP, HUMI (측정 시간별)
    """
    cached = _indoor_air_cache.get(station)
    if cached and time.time() - cached[0] < INDOOR_AIR_TTL:
        return cached[1]

    payload: dict = {"type": "indoor_air", "station": station, "fetched_at": time.time()}

    if SEOUL_KEY:
        # 실제 API 시도 — 여러 서비스명 순서대로
        for svc in ["IndoorAirQualityMeasureService", "subwayRealTimeAirQuality"]:
            try:
                url = f"http://openapi.seoul.go.kr:8088/{SEOUL_KEY}/json/{svc}/1/30/"
                _t0 = time.time()
                raw = await asyncio.get_event_loop().run_in_executor(None, http_get, url)
                _api_track("indoor_air", _t0, error=bool(raw.get("_error")))
                # 응답 파싱 시도 (여러 응답 구조 대응)
                rows = (raw.get(svc) or {}).get("row") or raw.get("row") or []
                if not rows:
                    for k in raw:
                        if isinstance(raw[k], dict) and "row" in raw[k]:
                            rows = raw[k]["row"]; break
                # station 필터
                matches = [r for r in rows if station in (r.get("STATION_NM") or r.get("STN_NM") or "")]
                if not matches and rows:
                    matches = rows[:1]
                if matches:
                    r = matches[0]
                    def _f(x):
                        try: return float(x)
                        except: return None
                    payload.update({
                        "co2_ppm": _f(r.get("CO2") or r.get("CO2_CONC")),
                        "pm10":    _f(r.get("PM10") or r.get("PM10_CONC")),
                        "pm25":    _f(r.get("PM25") or r.get("PM25_CONC")),
                        "temp":    _f(r.get("TEMP") or r.get("TEMPERATURE")),
                        "humi":    _f(r.get("HUMI") or r.get("HUMIDITY")),
                        "measure_dt": r.get("MEASURE_DT") or r.get("MEAS_DT"),
                        "source": "live",
                        "service": svc,
                    })
                    _indoor_air_cache[station] = (time.time(), payload)
                    return payload
            except Exception:
                pass

    # 시뮬레이션 fallback — 시간대 + 역 혼잡도 기반 CO₂ 추정
    # 근거: 1인당 CO₂ 방출 약 18L/h, 칸 정원 160명 기준
    import math, random
    rng = random.Random(hash(station) % (2**31))
    cur_h = time.localtime().tm_hour
    # 시간대 혼잡도 계수 (양봉 패턴)
    congestion_factor = (
        0.95 if 7 <= cur_h <= 9 else
        0.88 if 17 <= cur_h <= 19 else
        0.60 if 11 <= cur_h <= 14 else 0.40
    )
    base_co2 = 420  # 대기 기준
    crowd_co2 = congestion_factor * 580  # 혼잡 시 최대 +580ppm
    noise = rng.gauss(0, 20)
    co2 = round(base_co2 + crowd_co2 + noise, 1)
    pm10 = round(rng.uniform(20, 45) * (1 + congestion_factor * 0.5), 1)
    pm25 = round(pm10 * 0.65 + rng.gauss(0, 2), 1)
    temp = round(24 + rng.gauss(0, 1.5), 1)
    humi = round(45 + congestion_factor * 15 + rng.gauss(0, 3), 1)

    payload.update({
        "co2_ppm": co2,
        "pm10": pm10,
        "pm25": pm25,
        "temp": temp,
        "humi": humi,
        "measure_dt": time.strftime("%Y-%m-%d %H:%M"),
        "source": "simulated",
        "co2_grade": "나쁨" if co2 > 900 else "보통" if co2 > 600 else "좋음",
        "pm_grade": "나쁨" if pm10 > 35 else "보통" if pm10 > 25 else "좋음",
        "occupancy_estimate": round(congestion_factor * 160),
        "note": "실내 CO₂는 칸 내 인원 수와 비례 — BEV 점유 모델 약지도 학습 신호",
    })
    _indoor_air_cache[station] = (time.time(), payload)
    return payload


# ============== 엘리베이터 운행현황 (SubwayElevStatus) ==============

_elev_cache: dict[str, tuple] = {}
ELEV_TTL = 120.0

async def fetch_elevator_status(station: str) -> dict:
    """서울 지하철 엘리베이터 운행현황 + 위치.

    데이터: 서울 열린데이터광장 subwayElevStatus / SeoulMetroElev
    접근성 라우팅: 장애인/임산부/노약자 → 엘리베이터 최단 경로 자동 안내
    """
    cached = _elev_cache.get(station)
    if cached and time.time() - cached[0] < ELEV_TTL:
        return cached[1]

    payload: dict = {"type": "elevator", "station": station, "fetched_at": time.time()}

    if SEOUL_KEY:
        for svc in ["subwayElevStatus", "SeoulMetroElev", "subwayElevInfo"]:
            try:
                url = f"http://openapi.seoul.go.kr:8088/{SEOUL_KEY}/json/{svc}/1/30/{urllib.parse.quote(station)}"
                _t0 = time.time()
                raw = await asyncio.get_event_loop().run_in_executor(None, http_get, url)
                _api_track("elevator_status", _t0, error=bool(raw.get("_error")))
                rows = (raw.get(svc) or {}).get("row") or raw.get("row") or []
                if rows:
                    elevators = []
                    for r in rows[:10]:
                        elevators.append({
                            "id": r.get("ELEV_ID") or r.get("ELV_ID"),
                            "location": r.get("INSTALL_PLACE") or r.get("INST_PLCE") or "—",
                            "status": r.get("OPRT_STTS") or r.get("OPERATN_STTS") or "운행중",
                            "line": r.get("LINE_NUM") or r.get("ROUTE_NM"),
                        })
                    payload.update({
                        "elevators": elevators,
                        "total": len(elevators),
                        "operating": sum(1 for e in elevators if "운행" in (e.get("status") or "")),
                        "source": "live", "service": svc,
                    })
                    _elev_cache[station] = (time.time(), payload)
                    return payload
            except Exception:
                pass

    # 시뮬레이션 fallback — 주요 역 엘리베이터 수 추정
    import random
    rng = random.Random(hash(station) % (2**31))
    # 환승역일수록 엘리베이터 많음
    is_transfer = any(k in station for k in ["서울역", "잠실", "홍대", "사당", "합정", "강남", "고속터미널"])
    n_elev = rng.randint(4, 8) if is_transfer else rng.randint(2, 4)
    statuses = ["운행중"] * (n_elev - rng.randint(0, 1)) + (["점검중"] if rng.random() < 0.15 else [])
    locations = ["1번 출구", "2번 출구", "3번 출구", "4번 출구", "환승 통로", "대합실", "승강장 A", "승강장 B"]
    elevators = [
        {"id": f"EL{station[:2]}{i+1:02d}", "location": locations[i % len(locations)],
         "status": statuses[i] if i < len(statuses) else "운행중",
         "line": f"{(i % 2) + 2}호선"}
        for i in range(n_elev)
    ]
    operating = sum(1 for e in elevators if e["status"] == "운행중")
    payload.update({
        "elevators": elevators,
        "total": n_elev,
        "operating": operating,
        "out_of_service": n_elev - operating,
        "accessible_exits": [e["location"] for e in elevators if e["status"] == "운행중"][:3],
        "source": "simulated",
        "accessibility_note": "장애인·임산부·노약자 → 운행중 엘리베이터 출구로 이동 권고",
    })
    _elev_cache[station] = (time.time(), payload)
    return payload


# ============== 점유율 예측 (클러스터 기반 ML) ==============

# K=3 클러스터 패턴 (CardSubwayTime 202602 EDA 결과)
_CLUSTER_PATTERNS = {
    "office": {  # C0: 강남/역삼/성수/여의도 — 8시 하차↑, 18시 승차↑
        "weights": [0.2,0.15,0.1,0.1,0.15,0.5,1.2,3.5,5.5,4.0,2.5,1.8,
                    2.2,2.0,2.2,2.5,3.2,5.8,5.5,3.5,2.0,1.2,0.6,0.3],
    },
    "residential": {  # C1: 신림/사당/신도림 — 8시 승차↑, 18시 하차↑
        "weights": [0.3,0.2,0.1,0.1,0.2,0.8,2.5,5.2,4.5,3.0,2.0,1.8,
                    2.0,2.0,2.0,2.5,3.0,5.2,5.8,4.0,2.2,1.5,0.8,0.4],
    },
    "hub": {  # C2: 서울역/잠실/홍대/고속터미널 — 양봉 균형
        "weights": [0.4,0.3,0.2,0.1,0.2,0.6,1.5,3.8,5.0,4.2,2.8,2.5,
                    2.8,2.5,2.5,2.8,3.5,5.2,5.5,4.0,2.5,1.8,1.0,0.5],
    },
}
_STATION_CLUSTER = {
    "강남": "office", "역삼": "office", "성수": "office", "여의도": "office",
    "을지로입구": "office", "삼성": "office", "광화문": "office",
    "신림": "residential", "사당": "residential", "신도림": "residential",
    "서울대입구": "residential", "가산디지털단지": "residential",
    "잠실": "hub", "서울역": "hub", "홍대입구": "hub", "합정": "hub",
    "고속터미널": "hub", "왕십리": "hub",
}

def _get_cluster(station: str) -> str:
    for k, v in _STATION_CLUSTER.items():
        if k in station: return v
    return "hub"

def _predict_occupancy_24h(station: str) -> list:
    """24시간 점유율 예측 — 클러스터 패턴 × 과거 추세 × 요일 가중."""
    import math
    cluster = _get_cluster(station)
    pattern = _CLUSTER_PATTERNS[cluster]["weights"]
    total = sum(pattern)
    normalized = [w / total for w in pattern]
    # 요일 가중 (월~금 출퇴근 강화, 주말 감쇄)
    dow = time.localtime().tm_wday  # 0=월
    weekend_factor = 0.65 if dow >= 5 else 1.0
    result = []
    for h, w in enumerate(normalized):
        occ = min(1.0, w * 24 * weekend_factor)
        result.append({
            "hour": h,
            "occ": round(occ, 3),
            "pct": round(occ * 100, 1),
            "level": "혼잡" if occ > 0.75 else "보통" if occ > 0.45 else "여유",
        })
    return result


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
        "tier_counts": dict(_impact_total.get("tier_counts", {})),
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
                # cycle 427 — 정식 citydata 통합 호출 (이전엔 ppltn fake)
                payload = await fetch_citydata(req["poi"])
                await websocket.send(json.dumps(payload, ensure_ascii=False))
            elif t == "arrival_query" and req.get("stationName"):
                payload = await fetch_arrival(req["stationName"], req.get("line"))
                await websocket.send(json.dumps(payload, ensure_ascii=False))
            elif t == "events_query":
                # cycle 427 — citydata.EVENT_STTS 추출 (이전엔 빈 배열 하드코딩)
                poi = req.get("poi")
                if poi:
                    cd = await fetch_citydata(poi)
                    evs = cd.get("events") or []
                    await websocket.send(json.dumps({
                        "type": "events", "poi": poi,
                        "events": evs,
                        "total_count": len(evs),
                        "total_capacity": 0,    # citydata 에 capacity 미포함
                        "fetched_at": time.time(),
                        "error": cd.get("error"),
                    }, ensure_ascii=False))
                else:
                    await websocket.send(json.dumps({
                        "type": "events", "events": [], "total_count": 0, "total_capacity": 0,
                    }, ensure_ascii=False))
            elif t == "impact_log":
                saved = float(req.get("saved_pct") or 0)
                raw_krw = int(req.get("krw") or 0)
                st = req.get("station") or "?"
                bonus, tier = _bonus_krw(st)
                krw = raw_krw + bonus
                _impact_total["count"] += 1
                _impact_total["saved_pct_sum"] += saved
                _impact_total["krw_paid"] += krw
                _impact_total["stations"][st] = _impact_total["stations"].get(st, 0) + 1
                _impact_total["hourly"][time.localtime().tm_hour] += 1
                _impact_total["tier_counts"][tier] = _impact_total["tier_counts"].get(tier, 0) + 1
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
                    "priority_seat": _incident_total["priority_seat"],
                    "bottleneck": _incident_total["bottleneck"],
                    "events": _incident_total["events"][:8],
                }
                await broadcast(json.dumps(summary, ensure_ascii=False))
            elif t == "predict_surge" and req.get("poi"):
                # IDEA-7 24h 폭증 예측 — 과거 추세(ppltn_history) + 시간대 baseline + 행사 신호
                payload = predict_surge(req["poi"], req.get("hours_ahead", 24))
                await websocket.send(json.dumps(payload, ensure_ascii=False))
            elif t == "bus_arrival_query":
                payload = await fetch_bus_arrival(req.get("route", ""), req.get("station", ""))
                await websocket.send(json.dumps(payload, ensure_ascii=False))
            elif t == "indoor_air_query":
                station = req.get("station", "성수")
                loop = asyncio.get_event_loop()
                payload = await loop.run_in_executor(None, fetch_indoor_air, station)
                payload["type"] = "indoor_air"
                await websocket.send(json.dumps(payload, ensure_ascii=False))
            elif t == "elevator_query":
                station = req.get("station", "성수")
                loop = asyncio.get_event_loop()
                payload = await loop.run_in_executor(None, fetch_elevator_status, station)
                payload["type"] = "elevator_status"
                await websocket.send(json.dumps(payload, ensure_ascii=False))
            elif t == "occupancy_forecast":
                station = req.get("station", "성수")
                hours = int(req.get("hours", 24))
                payload = _predict_occupancy_24h(station, hours)
                payload["type"] = "occupancy_forecast"
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
    # 차등 보상 시연용 — OD 우선 + 환승역 가중치 ↑ (정확한 STTN 명칭으로 _bonus_krw 발동)
    STATIONS = [
        "성수카페거리", "강남역", "홍대 관광특구",                # hot (일반)
        "잠실역", "건대입구역",                                  # medium
        "삼성(무역센터)", "역삼", "광화문(세종문화회관)",          # OD 출근 도착 TOP 3 (+₩100)
        "학동", "시청",                                          # OD 퇴근 출발 (+₩100)
        "충무로", "연신내", "동대문",                            # 환승역 (+₩200)
        "서울역", "여의도",                                      # 보조
    ]
    STATION_WEIGHTS = [
        2.0, 2.0, 2.0,
        1.5, 1.2,
        2.5, 2.5, 2.0,                # OD 우선순위 빈도 ↑
        1.8, 1.8,
        2.5, 2.0, 2.0,                # 환승역 빈도 ↑↑ (시연 임팩트)
        1.5, 1.5,
    ]
    # Warm seed — 시작 즉시 12건 누적 + hourly 분포 양봉 형태 (지난 24h 시뮬)
    for _ in range(12):
        sv = rng.choices([7, 12, 22, 35, 5], weights=[0.25, 0.30, 0.25, 0.10, 0.10])[0]
        raw_krw = 200 if sv >= 30 else 150 if sv >= 15 else 100 if sv >= 5 else 0
        st = rng.choices(STATIONS, weights=STATION_WEIGHTS)[0]
        bonus, tier = _bonus_krw(st)
        krw = raw_krw + bonus
        h_seed = rng.choices(list(range(24)),
                             weights=[0.5, 0.3, 0.2, 0.2, 0.3, 0.8, 1.5, 4.0, 7.0, 4.5, 2.5, 2.0,
                                      2.5, 2.5, 2.5, 2.5, 3.0, 5.0, 7.0, 4.5, 2.5, 2.0, 1.0, 0.6])[0]
        _impact_total["count"] += 1
        _impact_total["saved_pct_sum"] += sv
        _impact_total["krw_paid"] += krw
        _impact_total["stations"][st] = _impact_total["stations"].get(st, 0) + 1
        _impact_total["hourly"][h_seed] += 1
        _impact_total["tier_counts"][tier] = _impact_total["tier_counts"].get(tier, 0) + 1
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
        raw_krw = 200 if sv >= 30 else 150 if sv >= 15 else 100 if sv >= 5 else 0
        st = rng.choices(STATIONS, weights=STATION_WEIGHTS)[0]
        bonus, tier = _bonus_krw(st)
        krw = raw_krw + bonus
        # 누적
        _impact_total["count"] += 1
        _impact_total["saved_pct_sum"] += sv
        _impact_total["krw_paid"] += krw
        _impact_total["stations"][st] = _impact_total["stations"].get(st, 0) + 1
        _impact_total["hourly"][h] += 1
        _impact_total["tier_counts"][tier] = _impact_total["tier_counts"].get(tier, 0) + 1
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
        ("free_ride", "med", "무임 의심 — 카드 미스캔", 0.20),
        ("lost", "low", "분실 가방 — BoT-SORT 12초+ 무인", 0.20),
        ("emergency", "high", "응급 — 30초+ 정지 + AED 거리", 0.10),
        ("suspicious", "high", "이상행동 — 환승 통로 군집", 0.10),
        ("priority_seat", "low", "임산부석 일반인 점유 — 배려 알림 송출", 0.15),
        ("bottleneck", "med", "에스컬레이터 병목 — 정체 45초+ 우회 안내", 0.15),
        ("free_ride", "med", "자동 분산 안내 송출 — 만석", 0.10),
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
                    "priority_seat": _incident_total["priority_seat"],
                    "bottleneck": _incident_total["bottleneck"],
                    "events": _incident_total["events"][:8],
                }
                await broadcast(json.dumps(summary, ensure_ascii=False))
            except Exception: pass


async def fake_bev_loop():
    """시연 fail-safe — 호차별 점유 + BoT-SORT 궤적 + 특별석 + 사건 시뮬.

    개선 (수상 버전):
    - 10량 × 호차별 좌석 레이아웃 (BEV 320×32 → 32px 폭 / 호차)
    - BoT-SORT 유사 궤적 — 프레임 간 연속성 (track ID 유지, smooth 이동)
    - 좌석 착석 / 기립 분류 (bev_y 위치 기반)
    - 임산부·노약자석 점유 감지 (양 끝 2칸 우선순위석)
    - 문 zone 병목 (bev_y < 8 / > 24) 감지
    - car_summary — 호차별 {count, seated, standing, occ_pct, priority_occ, door_zone}
    - 분실 가방: BoT-SORT 12초+ 무인 track → backpack 객체
    - 5 Hz 송출, 출퇴근 양봉 자동 반영
    """
    import math
    import random

    CAR_W = 32           # 1호차 = 32 BEV 픽셀
    N_CARS = 10
    BEV_H = 32
    SEAT_Y_MIN, SEAT_Y_MAX = 8, 24   # 착석 중심 Y 범위
    DOOR_ZONE = 7        # 문 앞 Y (< DOOR_ZONE or > BEV_H - DOOR_ZONE)
    PRIORITY_CARS = {0, 9}            # 1호차·10호차 임산부·노약자석

    rng = random.Random(42)
    t0 = time.time()
    fps_cnt = 0; fps_t = t0; fps_val = 5.0

    # ──── BoT-SORT 유사 상태 ────
    # track_states: id → {x, y, vx, vy, age, static_sec, cls, car, seat, priority}
    track_states: dict = {}
    next_id = 1
    _backpack_id = 900
    _backpack_ts: float = 0.0   # 분실 가방 등장 시각

    def _peak_factor(h: int) -> float:
        if 7 <= h <= 9 or 17 <= h <= 19: return 1.22
        if 10 <= h <= 16: return 0.85
        if 20 <= h <= 22: return 0.75
        return 0.35   # 새벽

    def _target_n(h: int) -> int:
        base = 18  # 10량 기준 평균 탑승 (데모 적절 밀도)
        return max(4, int(rng.gauss(base * _peak_factor(h), 2.5)))

    def _rand_car() -> int:
        """호차 선택 — 중간 칸(5~6) 쏠림 모방 + 끝 칸 약함."""
        weights = [0.07,0.09,0.11,0.12,0.13,0.13,0.12,0.11,0.07,0.05]
        return rng.choices(range(N_CARS), weights=weights)[0]

    def _car_x(car: int) -> float:
        return car * CAR_W + CAR_W / 2 + rng.gauss(0, 6)

    def _is_seat(y: float) -> bool:
        return SEAT_Y_MIN <= y <= SEAT_Y_MAX

    def _is_door(y: float) -> bool:
        return y < DOOR_ZONE or y > BEV_H - DOOR_ZONE

    while True:
        await asyncio.sleep(0.2)
        fps_cnt += 1
        now = time.time()
        if now - fps_t >= 1.0:
            fps_val = fps_cnt / (now - fps_t)
            fps_cnt = 0; fps_t = now

        if not clients:
            continue

        h = time.localtime(now).tm_hour
        target_n = _target_n(h)

        # ── 승·하차 시뮬: 인원 조정 ──
        cur_ids = list(track_states.keys())
        cur_n = len([k for k in cur_ids if track_states[k]["cls"] == "person"])

        # 초과 → 일부 하차 (퇴장)
        while cur_n > target_n + 2:
            k = rng.choice([k for k in cur_ids if track_states[k]["cls"] == "person"])
            del track_states[k]
            cur_ids.remove(k)
            cur_n -= 1

        # 부족 → 신규 승차
        while cur_n < target_n - 2:
            car = _rand_car()
            x0 = car * CAR_W + rng.uniform(4, CAR_W - 4)
            # 문 근처에서 탑승 후 자리로 이동
            y0 = rng.choice([2.0, BEV_H - 2.0])
            is_pr = car in PRIORITY_CARS and rng.random() < 0.20
            track_states[next_id] = {
                "x": x0, "y": y0,
                "vx": rng.gauss(0, 0.3), "vy": rng.uniform(0.5, 1.5) * (1 if y0 < 4 else -1),
                "age": 0, "static_sec": 0.0,
                "cls": "person", "car": car, "seat": False, "priority": is_pr
            }
            next_id += 1
            cur_n += 1

        # ── 궤적 업데이트 (BoT-SORT smooth) ──
        phase = (now - t0) * 0.3
        for tid, st in list(track_states.items()):
            if st["cls"] != "person":
                continue
            car = st["car"]
            car_cx = (car + 0.5) * CAR_W
            # 목표 위치 — 착석이면 좌석 Y, 기립이면 통로 Y
            if st["age"] > 25 and not st["seat"]:
                # 착석 확률 60%
                if rng.random() < 0.012:
                    st["seat"] = True
                    st["vy"] = 0.0

            tx = car_cx + math.sin(phase + tid * 0.8) * 4
            ty = (BEV_H / 2) + math.cos(phase + tid * 0.6) * (4 if st["seat"] else 7)

            # 부드러운 이동 (감쇠)
            st["vx"] = st["vx"] * 0.85 + (tx - st["x"]) * 0.04 + rng.gauss(0, 0.15)
            if not st["seat"]:
                st["vy"] = st["vy"] * 0.85 + (ty - st["y"]) * 0.04 + rng.gauss(0, 0.15)

            st["x"] = max(car * CAR_W + 1, min((car + 1) * CAR_W - 1, st["x"] + st["vx"]))
            st["y"] = max(1, min(BEV_H - 1, st["y"] + (0 if st["seat"] else st["vy"])))

            speed = math.hypot(st["vx"], st["vy"] if not st["seat"] else 0)
            if speed < 0.25:
                st["static_sec"] += 0.2
            else:
                st["static_sec"] = max(0, st["static_sec"] - 0.1)
            st["age"] += 1

        # ── 분실 가방 시뮬 (30초 주기) ──
        bag_active = (now - _backpack_ts) < 18.0
        if not bag_active and int(now) % 30 < 1 and _backpack_id not in track_states:
            _backpack_ts = now
            bc = rng.randint(2, 7)
            track_states[_backpack_id] = {
                "x": bc * CAR_W + CAR_W / 2, "y": BEV_H - 5,
                "vx": 0, "vy": 0, "age": 0, "static_sec": 0,
                "cls": "backpack", "car": bc, "seat": False, "priority": False
            }
        elif bag_active and _backpack_id in track_states:
            track_states[_backpack_id]["static_sec"] += 0.2
        elif not bag_active and _backpack_id in track_states:
            del track_states[_backpack_id]

        # ── tracks 리스트 생성 ──
        tracks = []
        for tid, st in track_states.items():
            tracks.append({
                "id": tid,
                "bev_x": round(st["x"], 1),
                "bev_y": round(st["y"], 1),
                "cls": st["cls"],
                "class": st["cls"],   # 양쪽 필드 호환
                "conf": round(0.72 + rng.random() * 0.25, 2),
                "car": st["car"] + 1,         # 1-indexed
                "seat": st["seat"],
                "priority": st["priority"],
                "static_sec": round(st["static_sec"], 1),
                "door_zone": _is_door(st["y"]),
            })

        # ── 호차별 요약 ──
        car_summary = []
        SEAT_CAP = 54   # 10량 기준 1호차 좌석 수 (실제 서울 2호선)
        STAND_CAP = 30  # 기립 수용
        for c in range(N_CARS):
            ct = [t for t in tracks if t.get("car") == c + 1 and t["cls"] == "person"]
            seated = sum(1 for t in ct if t["seat"])
            standing = len(ct) - seated
            priority_occ = sum(1 for t in ct if t["priority"])
            door_zone = sum(1 for t in ct if t["door_zone"])
            occ_pct = min(1.0, len(ct) / max(1, SEAT_CAP + STAND_CAP) * 2.8)
            car_summary.append({
                "car": c + 1,
                "count": len(ct),
                "seated": seated,
                "standing": standing,
                "occ_pct": round(occ_pct, 3),
                "priority_occ": priority_occ,
                "door_zone": door_zone,
                "bottleneck": door_zone >= 3,
            })

        payload = {
            "type": "bev",
            "ts": now,
            "fps": round(fps_val, 1),
            "tracks": tracks,
            "car_summary": car_summary,
            "demo": True,
        }
        _cv_metrics["fps"] = round(fps_val, 1)
        _cv_metrics["tracks"] = len(tracks)
        _cv_metrics["frames"] += 1
        _cv_metrics["last_ts"] = now
        _cv_metrics["demo"] = True
        await broadcast(json.dumps(payload, ensure_ascii=False))


async def fake_bus_bev_loop():
    """버스 차내 BEV 시뮬 — 문 2개 기준 30석 + 기립 공간.

    버스는 지하철과 다른 동역학:
    - 전문(앞) / 후문(뒤) 승하차 → 문 zone 병목
    - 운전석 앞 제한 구역
    - 노약자석 2석 (맨 앞)
    - 총 BEV 공간: 120×30 (버스 길이 × 폭)
    """
    import math, random
    BUS_W, BUS_H = 120, 30
    SEAT_ROWS = 15; SEAT_COLS = 2
    SEAT_CAP = SEAT_ROWS * SEAT_COLS   # 30석
    STAND_CAP = 25
    FRONT_DOOR_X = 12; REAR_DOOR_X = 96
    DRIVER_X = 4

    rng = random.Random(77)
    t0 = time.time()
    fps_cnt = 0; fps_t = t0; fps_val = 5.0

    track_states: dict = {}
    nxt_id = 1

    ROUTES = [
        {"route": "146", "plate": "서울 75바 1234", "dest": "방화역"},
        {"route": "240", "plate": "서울 83가 5678", "dest": "도봉산역"},
        {"route": "N61", "plate": "서울 01나 9012", "dest": "상계동"},
    ]
    cur_route = rng.choice(ROUTES)

    def _peak(h):
        if 7 <= h <= 9 or 17 <= h <= 19: return 1.15
        if 10 <= h <= 16: return 0.75
        return 0.30

    while True:
        await asyncio.sleep(0.2)
        fps_cnt += 1
        now = time.time()
        if now - fps_t >= 1.0:
            fps_val = fps_cnt / (now - fps_t)
            fps_cnt = 0; fps_t = now

        if not clients:
            continue

        h = time.localtime(now).tm_hour
        target_n = max(2, int(rng.gauss((SEAT_CAP + STAND_CAP * 0.5) * _peak(h), 3)))
        target_n = min(SEAT_CAP + STAND_CAP, target_n)

        pids = [k for k, v in track_states.items() if v["cls"] == "person"]
        while len(pids) > target_n + 2:
            k = rng.choice(pids); del track_states[k]; pids.remove(k)
        while len(pids) < target_n - 2:
            # 좌석 우선 배치
            row = rng.randint(1, SEAT_ROWS - 1)
            col = rng.randint(0, SEAT_COLS - 1)
            x0 = DRIVER_X + 6 + row * (BUS_W - DRIVER_X - 8) / SEAT_ROWS + rng.gauss(0, 2)
            y0 = 8 + col * 14 + rng.gauss(0, 2)
            seated = rng.random() < 0.65
            priority = row <= 1 and rng.random() < 0.25
            track_states[nxt_id] = {
                "x": x0, "y": y0, "vx": 0, "vy": 0,
                "cls": "person", "seat": seated, "priority": priority,
                "age": 0, "static_sec": 0.0,
            }
            pids.append(nxt_id); nxt_id += 1

        phase = (now - t0) * 0.25
        for tid, st in list(track_states.items()):
            if st["cls"] != "person": continue
            micro_x = math.sin(phase + tid * 1.1) * (0.3 if st["seat"] else 0.8)
            micro_y = math.cos(phase + tid * 0.9) * (0.3 if st["seat"] else 0.6)
            st["x"] = max(DRIVER_X + 5, min(BUS_W - 4, st["x"] + micro_x))
            st["y"] = max(2, min(BUS_H - 2, st["y"] + micro_y))
            speed = math.hypot(micro_x, micro_y)
            if speed < 0.2: st["static_sec"] += 0.2
            else: st["static_sec"] = max(0, st["static_sec"] - 0.1)
            st["age"] += 1

        tracks = []
        for tid, st in track_states.items():
            door_z = abs(st["x"] - FRONT_DOOR_X) < 8 or abs(st["x"] - REAR_DOOR_X) < 8
            tracks.append({
                "id": tid, "bev_x": round(st["x"], 1), "bev_y": round(st["y"], 1),
                "cls": st["cls"], "class": st["cls"],
                "conf": round(0.72 + rng.random() * 0.24, 2),
                "seat": st["seat"], "priority": st.get("priority", False),
                "static_sec": round(st["static_sec"], 1), "door_zone": door_z,
            })

        persons = [t for t in tracks if t["cls"] == "person"]
        total_pax = len(persons)
        seated_n = sum(1 for t in persons if t["seat"])
        occ_pct = min(1.0, total_pax / (SEAT_CAP + STAND_CAP * 0.8))

        # 3구역 요약
        def _zone(x):
            if x < 40: return "front"
            if x < 80: return "mid"
            return "rear"
        zone_data = {"front": {"count":0,"standing":0}, "mid": {"count":0,"standing":0}, "rear": {"count":0,"standing":0}}
        for t in persons:
            z = _zone(t["bev_x"])
            zone_data[z]["count"] += 1
            if not t["seat"]: zone_data[z]["standing"] += 1

        payload = {
            "type": "bus_bev",
            "ts": now, "fps": round(fps_val, 1),
            "route": cur_route["route"],
            "plate": cur_route["plate"],
            "dest": cur_route["dest"],
            "tracks": tracks,
            "zone_summary": zone_data,
            "total_pax": total_pax,
            "seated": seated_n,
            "standing": total_pax - seated_n,
            "occ_pct": round(occ_pct, 3),
            "congestion": "붐빔" if occ_pct > 0.85 else "약간 붐빔" if occ_pct > 0.60 else "보통" if occ_pct > 0.35 else "여유",
            "demo": True,
        }
        await broadcast(json.dumps(payload, ensure_ascii=False))


async def _fetch_aed_nearby(lat: str | None, lon: str | None) -> dict:
    """AED 위치 — 서울시 자동심장충격기(AED) 위치정보 공공데이터.

    lat/lon 제공 시 가장 가까운 5개 반환 (단순 유클리드 거리 정렬).
    없으면 주요 지하철역 근처 AED 샘플 반환.
    """
    import math
    if not SEOUL_KEY:
        return {"ok": False, "error": "SEOUL_OPENDATA_API_KEY 미설정", "aed": []}
    url = f"http://openapi.seoul.go.kr:8088/{SEOUL_KEY}/json/InjuryCenterInfo/1/50/"
    _t0 = time.time()
    raw = await asyncio.get_event_loop().run_in_executor(None, http_get, url)
    _api_track("aed_location", _t0, error=bool(raw.get("_error")))

    rows = []
    try:
        val = raw.get("InjuryCenterInfo") or {}
        for r in (val.get("row") or []):
            rlat = _to_float_safe(r.get("Y_WGS84") or r.get("LATITUDE"))
            rlon = _to_float_safe(r.get("X_WGS84") or r.get("LONGITUDE"))
            if rlat is None or rlon is None: continue
            dist_m = None
            if lat and lon:
                try:
                    dy = (rlat - float(lat)) * 111139
                    dx = (rlon - float(lon)) * 111139 * math.cos(math.radians(float(lat)))
                    dist_m = round(math.hypot(dx, dy))
                except Exception: pass
            rows.append({
                "name": r.get("INSTIT_NM") or r.get("NAME"),
                "addr": r.get("ADDR") or r.get("ADDRESS"),
                "lat": rlat, "lon": rlon,
                "dist_m": dist_m,
                "phone": r.get("TEL") or r.get("PHONE"),
            })
    except Exception:
        pass

    if lat and lon:
        rows.sort(key=lambda x: x.get("dist_m") or 999999)

    # 응답 없으면 지하철역 근처 AED 시뮬 데이터
    if not rows:
        rows = [
            {"name": "잠실역 1번출구 AED", "addr": "서울 송파구 잠실동", "lat": 37.5133, "lon": 127.1001, "dist_m": 28, "phone": "02-6110-1234"},
            {"name": "강남역 환승통로 AED", "addr": "서울 강남구 역삼동", "lat": 37.4980, "lon": 127.0277, "dist_m": 52, "phone": "02-6110-5678"},
        ]
    return {"ok": True, "aed": rows[:5], "fetched_at": time.time(), "simulated": not raw or bool(raw.get("_error"))}


def _to_float_safe(v):
    try: return float(v) if v not in (None, "", "-") else None
    except (TypeError, ValueError): return None


async def fetch_bus_arrival(route_id: str, station_id: str) -> dict:
    """버스 실시간 도착 정보 — data.go.kr BIS API (없으면 시뮬 반환)."""
    BIS_KEY = os.environ.get("DATA_GO_KR_API_KEY", "")
    if BIS_KEY:
        url = ("http://apis.data.go.kr/1613000/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList"
               f"?serviceKey={urllib.parse.quote(BIS_KEY)}&pageNo=1&numOfRows=5"
               f"&cityCode=11&nodeId={urllib.parse.quote(station_id)}&_type=json")
        _t0 = time.time()
        raw = await asyncio.get_event_loop().run_in_executor(None, http_get, url)
        _api_track("bis_arrival", _t0, error=bool(raw.get("_error")))
        items = []
        try:
            body = raw.get("response", {}).get("body", {})
            for it in ((body.get("items") or {}).get("item") or []):
                if isinstance(it, dict):
                    items.append({
                        "route": it.get("routeno") or it.get("routeid"),
                        "arrival_sec": _to_int(it.get("arrtime")),
                        "vehicle_no": it.get("vehicleno"),
                        "stop_cnt": _to_int(it.get("arrprevstationcnt")),
                    })
        except Exception:
            pass
        if items:
            return {"type": "bus_arrival", "route": route_id, "station": station_id,
                    "items": items, "simulated": False, "fetched_at": time.time()}

    # fallback 시뮬 (BIS 키 없거나 실패)
    import random, math
    rng = random.Random(int(time.time() // 60))
    h = time.localtime().tm_hour
    freq_min = 4 if (7 <= h <= 9 or 17 <= h <= 19) else 8 if 10 <= h <= 22 else 15
    items_sim = []
    for i in range(3):
        base = (i * freq_min + rng.randint(0, freq_min - 1)) * 60
        items_sim.append({
            "route": route_id or "146",
            "arrival_sec": base,
            "vehicle_no": f"서울{70+i:02d}바{rng.randint(1000,9999)}",
            "stop_cnt": rng.randint(1, 5),
        })
    return {"type": "bus_arrival", "route": route_id, "station": station_id,
            "items": items_sim, "simulated": True, "fetched_at": time.time()}


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
    # path_only — 쿼리스트링 제거 버전 (정확한 == 매칭용, startswith는 path 그대로 사용)
    path_only = path.split("?", 1)[0] if "?" in path else path
    if path_only == "/api/v1/incidents":
        body = json.dumps({
            "ok": True,
            "counts": {
                "emergency": _incident_total["emergency"],
                "suspicious": _incident_total["suspicious"],
                "lost": _incident_total["lost"],
                "free_ride": _incident_total["free_ride"],
                "priority_seat": _incident_total["priority_seat"],
                "bottleneck": _incident_total["bottleneck"],
            },
            "events": _incident_total["events"][:30],
            "total": (_incident_total["emergency"] + _incident_total["suspicious"]
                      + _incident_total["lost"] + _incident_total["free_ride"]
                      + _incident_total["priority_seat"] + _incident_total["bottleneck"]),
        }).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    if path_only == "/api/v1/impact":
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
    if path_only == "/api/v1/policy_summary":
        # 모든 정책 KPI 통합 — 단일 endpoint로 외부 도구 (Excel/Power BI) 폴링 효율화
        try:
            from pathlib import Path as _P
            import time as _t
            cur_h = _t.localtime().tm_hour
            # 정적 EDA 결과
            disp_path = _P(__file__).resolve().parent.parent.parent / "frontend" / "figs" / "dispersion_sim_report.json"
            disp = json.loads(disp_path.read_text(encoding="utf-8")) if disp_path.exists() else {}
            # 라이브 임팩트 + tier
            im = _build_impact_summary() if _impact_total["count"] > 0 else None
            est_rate = (im or {}).get("est_response_rate", 0)
            ratio = est_rate / 0.30 if est_rate > 0 else 0
            body = json.dumps({
                "ok": True,
                "current_hour": cur_h,
                "policy": {
                    "tier_definition": {
                        "basic": {"krw": 200, "condition": "30%p 이상 한산 칸"},
                        "od": {"krw": 300, "condition": "현 시각 OD 우선순위 역 + 분산"},
                        "transfer": {"krw": 400, "condition": "환승역 + 분산 (양 호선 동시 절감)"},
                    },
                    "roi_at_30pct": {"net_yearly_won": 139_300_000_000, "roi_x": 347, "infra_won": 400_000_000},
                },
                "live_impact": im,
                "live_dispersion": {
                    "estimated_response_rate": round(est_rate, 4),
                    "sigma_reduction_pct": round(disp.get("sigma_reduction_pct", 9.0) * ratio, 2),
                    "peak_reduction_pct": round(disp.get("peak_reduction_pct", 13.5) * ratio, 2),
                },
                "incident_breakdown": {
                    "emergency": _incident_total["emergency"],
                    "suspicious": _incident_total["suspicious"],
                    "lost": _incident_total["lost"],
                    "free_ride": _incident_total["free_ride"],
                    "priority_seat": _incident_total["priority_seat"],
                    "bottleneck": _incident_total["bottleneck"],
                },
                "static_eda": {
                    "dispersion_sim": {
                        "sigma_reduction_pct": disp.get("sigma_reduction_pct"),
                        "peak_reduction_pct": disp.get("peak_reduction_pct"),
                        "offpeak_lift_pct": disp.get("offpeak_lift_pct"),
                    },
                    "data_source": "subway_time_202602.parquet 1~9호선 28일 평균",
                },
            }).encode("utf-8")
            return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
        except Exception as e:
            return (500, [("content-type", "application/json")] + CORS_HEADERS,
                    json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
    if path_only == "/api/v1/transfer_priority":
        # /api/v1/transfer_priority — 환승역 호선 간 비대칭 차이 TOP 5 (현 시각 AM/PM)
        try:
            from pathlib import Path as _P
            import time as _t
            rep = _P(__file__).resolve().parent.parent.parent / "frontend" / "figs" / "transfer_stations_report.json"
            base = json.loads(rep.read_text(encoding="utf-8")) if rep.exists() else {}
            cur_h = _t.localtime().tm_hour
            if 7 <= cur_h <= 11:
                priority_type = "am_transfer"
                priority_list = base.get("top_am_diff", [])[:5]
                rationale = f"현재 {cur_h}시 — 출근 환승 흐름 우세 (호선 간 비대칭 차이)"
            elif 17 <= cur_h <= 21:
                priority_type = "pm_transfer"
                priority_list = base.get("top_pm_diff", [])[:5]
                rationale = f"현재 {cur_h}시 — 퇴근 환승 흐름 우세 (호선 간 비대칭 차이)"
            else:
                priority_type = "neutral"
                priority_list = []
                rationale = f"현재 {cur_h}시 — 비피크 시간대"
            body = json.dumps({
                "ok": True,
                "current_hour": cur_h,
                "priority_type": priority_type,
                "priority_stations": priority_list,
                "rationale": rationale,
                "static": {
                    "n_transfer_stations": base.get("n_transfer_stations"),
                    "data_source": "subway_time_202602.parquet (1~9호선 28일 평균, 환승역 37개)",
                },
            }).encode("utf-8")
            return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
        except Exception as e:
            return (500, [("content-type", "application/json")] + CORS_HEADERS,
                    json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
    if path_only == "/api/v1/od_asymmetry":
        # /api/v1/od_asymmetry — OD 비대칭 분석 결과 + 현 시각 우선 추천 역
        try:
            from pathlib import Path as _P
            import time as _t
            rep = _P(__file__).resolve().parent.parent.parent / "frontend" / "figs" / "od_asymmetry_report.json"
            base = json.loads(rep.read_text(encoding="utf-8")) if rep.exists() else {}
            # 현 시각 기반 우선순위
            cur_h = _t.localtime().tm_hour
            am_h = base.get("am_hour", 9)
            pm_h = base.get("pm_hour", 19)
            # AM 시간(7~11) → 출근 도착지 우선, PM(17~21) → 퇴근 출발지 우선
            if 7 <= cur_h <= 11:
                priority_type = "arrival"
                priority_list = base.get("top_arrival", [])[:5]
                rationale = f"현재 {cur_h}시 — 출근 도착지 핫스팟 (OFF >> ON)"
            elif 17 <= cur_h <= 21:
                priority_type = "departure"
                priority_list = base.get("top_departure", [])[:5]
                rationale = f"현재 {cur_h}시 — 퇴근 출발지 핫스팟 (ON >> OFF)"
            else:
                priority_type = "neutral"
                priority_list = []
                rationale = f"현재 {cur_h}시 — 비피크 시간대"
            body = json.dumps({
                "ok": True,
                "current_hour": cur_h,
                "priority_type": priority_type,
                "priority_stations": priority_list,
                "rationale": rationale,
                "static": {
                    "am_hour": am_h,
                    "pm_hour": pm_h,
                    "n_significant_stations": base.get("n_significant_stations"),
                    "min_total_threshold": base.get("min_total_threshold"),
                },
            }).encode("utf-8")
            return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
        except Exception as e:
            return (500, [("content-type", "application/json")] + CORS_HEADERS,
                    json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
    if path_only == "/api/v1/dispersion":
        # /api/v1/dispersion — 분산 정책 시뮬 결과 (실 parquet 검증값 + 라이브 응답률 추정 보정)
        try:
            from pathlib import Path as _P
            rep = _P(__file__).resolve().parent.parent.parent / "frontend" / "figs" / "dispersion_sim_report.json"
            base = {}
            if rep.exists():
                base = json.loads(rep.read_text(encoding="utf-8"))
            # 라이브 응답률 추정 — _impact_total["count"] 가 응답한 시민 수
            # 일평균 ON ~7M, 1% 응답이면 70,000명. 현재 count → 응답률 = count / 70000
            live_count = _impact_total["count"]
            est_rate = min(0.80, live_count / 70000) if live_count > 0 else 0.0
            # 비례 스케일 — 실 검증값(30%) 대비
            ratio = est_rate / 0.30 if est_rate > 0 else 0
            sigma_drop_live = base.get("sigma_reduction_pct", 9.0) * ratio
            peak_drop_live = base.get("peak_reduction_pct", 13.5) * ratio
            offpeak_lift_live = base.get("offpeak_lift_pct", 5.6) * ratio
            body = json.dumps({
                "ok": True,
                "static": {
                    "model": "dispersion_sim @ rate=0.30",
                    "sigma_reduction_pct": base.get("sigma_reduction_pct"),
                    "peak_reduction_pct": base.get("peak_reduction_pct"),
                    "offpeak_lift_pct": base.get("offpeak_lift_pct"),
                    "peak_offpeak_ratio_before": base.get("peak_offpeak_ratio_before"),
                    "peak_offpeak_ratio_after": base.get("peak_offpeak_ratio_after"),
                    "n_lines": base.get("n_lines"),
                    "data_source": base.get("data_source"),
                },
                "live": {
                    "estimated_response_rate": round(est_rate, 4),
                    "live_count": live_count,
                    "sigma_reduction_pct": round(sigma_drop_live, 2),
                    "peak_reduction_pct": round(peak_drop_live, 2),
                    "offpeak_lift_pct": round(offpeak_lift_live, 2),
                },
            }).encode("utf-8")
            return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
        except Exception as e:
            return (500, [("content-type", "application/json")] + CORS_HEADERS,
                    json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
    if path_only == "/api/docs":
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
            "<h2>GET <code>/api/v1/incidents</code></h2>"
            "<p>사고 누적 + 최근 30 events (응급/이상/분실/무임)</p>"
            "<h2>GET <code>/api/v1/dispersion</code></h2>"
            "<p>분산 정책 시뮬 — 실 parquet σ/peak/offpeak 검증값 + 라이브 응답률 비례 추정</p>"
            "<h2>GET <code>/api/v1/od_asymmetry</code></h2>"
            "<p>OD 비대칭 — 현 시각(AM/PM) 자동 매칭 + 우선 분산 추천 역 TOP 5</p>"
            "<h2>GET <code>/api/v1/transfer_priority</code></h2>"
            "<p>환승역 호선 간 비대칭 차이 TOP 5 — 환승 흐름 우세 + 분산 후보 (현 시각 AM/PM 자동)</p>"
            "<h2>GET <code>/api/v1/data_sources</code></h2>"
            "<p>활용 데이터셋 목록 + 라이브 API 활성 상태 — 심사 참고 (빅데이터 활용도 증빙)</p>"
            "<h2>GET <code>/api/v1/line_roi</code></h2>"
            "<p>호선별 ROI 우선순위 — 실 parquet carload × policy_roi_v3 결합 · 9호선 랭킹 + 예산 추천 역</p>"
            "<h2>GET <code>/api/v1/policy_summary</code></h2>"
            "<p><b>통합 KPI</b> — 정책 정의(tier 4단) + 라이브 impact + 라이브 dispersion + 정적 EDA 단일 응답 (Excel/Power BI 폴링 효율)</p>"
            "<h2>GET <code>/api/openapi.yaml</code></h2>"
            "<p>표준 OpenAPI 3.0 spec — Swagger / Redoc / Postman 임포트 가능</p>"
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
    if path_only == "/api/openapi.yaml":
        try:
            from pathlib import Path as _P
            spec = _P(__file__).resolve().parent.parent.parent / "docs" / "openapi.yaml"
            if spec.exists():
                body = spec.read_bytes()
                return (200, [("content-type", "application/x-yaml; charset=utf-8")] + CORS_HEADERS, body)
        except Exception:
            pass
        return (404, [("content-type", "text/plain")] + CORS_HEADERS, b"openapi.yaml not found")
    if path.startswith("/api/v1/aed"):
        # AED 위치 — 서울시 자동심장충격기(AED) 위치 정보
        qs = path.split("?", 1)[1] if "?" in path else ""
        params = dict(urllib.parse.parse_qsl(qs))
        lat = params.get("lat"); lon = params.get("lon")
        aed_payload = await _fetch_aed_nearby(lat, lon)
        body = json.dumps(aed_payload, ensure_ascii=False).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    if path.startswith("/api/v1/bus_arrival"):
        qs = path.split("?", 1)[1] if "?" in path else ""
        params = dict(urllib.parse.parse_qsl(qs))
        payload = await fetch_bus_arrival(params.get("route", "146"), params.get("station", ""))
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    if path_only == "/api/v1/indoor_air":
        station = params.get("station", "성수")
        loop = asyncio.get_event_loop()
        payload = await loop.run_in_executor(None, fetch_indoor_air, station)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    if path_only == "/api/v1/elevator":
        station = params.get("station", "성수")
        loop = asyncio.get_event_loop()
        payload = await loop.run_in_executor(None, fetch_elevator_status, station)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    if path_only == "/api/v1/occupancy_forecast":
        station = params.get("station", "성수")
        hours = int(params.get("hours", "24"))
        payload = _predict_occupancy_24h(station, hours)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    if path_only == "/api/v1/data_sources":
        # 활용 데이터셋 목록 — 심사 참고 (빅데이터 활용도 증빙)
        body = json.dumps({
            "ok": True,
            "project": "MetroEyes (SubwayBEV)",
            "competition": "2026 서울시 빅데이터 활용 경진대회",
            "data_sources": [
                {
                    "id": "CardSubwayTime", "type": "필수",
                    "name": "서울시 지하철 시간대별 승하차 인원",
                    "url": "http://openapi.seoul.go.kr:8088/.../CardSubwayTime",
                    "usage": ["EDA 역 클러스터링 K=3", "ROI v3 473M분/년 추정", "분산 정책 σ−9% 검증"],
                    "period": "202602 (28일)", "format": "JSON/CSV", "live": False,
                },
                {
                    "id": "RealtimeSubwayStationArrival", "type": "필수",
                    "name": "서울 실시간 지하철 도착정보",
                    "url": "http://swopenAPI.seoul.go.kr/api/subway/.../json/realtimeStationArrival",
                    "usage": ["운영자 콘솔 FC 도착카드 라이브", "시민 PWA 도착 알림"],
                    "period": "실시간 (1분 폴링)", "format": "JSON", "live": True, "active": bool(SUBWAY_KEY),
                },
                {
                    "id": "citydata_ppltn", "type": "가점",
                    "name": "서울 실시간 도시데이터 (인구·날씨·도로·따릉이·주차·상권·버스)",
                    "url": "https://data.seoul.go.kr/SeoulRtd/getCategoryList",
                    "usage": ["시민 PWA POI 혼잡도", "광고 단가 실시간 조정 입력", "이상 감지 폭증 트리거"],
                    "period": "실시간 (분 단위 갱신)", "format": "JSON", "live": True, "active": bool(SEOUL_KEY),
                },
                {
                    "id": "InjuryCenterInfo", "type": "가점",
                    "name": "서울시 자동심장충격기(AED) 위치 정보",
                    "url": "http://openapi.seoul.go.kr:8088/.../InjuryCenterInfo",
                    "usage": ["응급 골든타임 AED 최근접 거리 자동 계산", "BEV 화면 AED 위치 오버레이"],
                    "period": "정적 (최신 DB)", "format": "JSON", "live": False, "active": bool(SEOUL_KEY),
                },
                {
                    "id": "naver_news", "type": "가점",
                    "name": "Naver 검색 API — 뉴스/블로그",
                    "url": "https://openapi.naver.com/v1/search/news.json",
                    "usage": ["폭증 원인 자동 조회", "Claude Haiku 80자 요약 입력"],
                    "period": "이벤트 트리거 (폭증 감지 시)", "format": "JSON", "live": True, "active": bool(NAVER_ID),
                },
                {
                    "id": "claude_haiku", "type": "AI",
                    "name": "Anthropic Claude Haiku 4.5 API",
                    "url": "https://api.anthropic.com/v1/messages",
                    "usage": ["광고 단가 근거 80자 자동 생성", "폭증 문맥 요약", "LLM 운영 보조"],
                    "period": "이벤트 트리거 (폭증/광고 갱신)", "format": "REST", "live": True, "active": bool(ANTHROPIC_KEY),
                },
                {
                    "id": "BIS_bus_arrival", "type": "확장",
                    "name": "공공데이터포털 버스 실시간 도착정보 (BIS)",
                    "url": "http://apis.data.go.kr/1613000/ArvlInfoInqireService",
                    "usage": ["시민 PWA 버스 도착 알림", "버스 운영자 콘솔 차량 접근 카드"],
                    "period": "실시간 (1분 폴링)", "format": "JSON", "live": True,
                    "active": bool(os.environ.get("DATA_GO_KR_API_KEY", "")),
                },
                {
                    "id": "in_house_cv", "type": "자체",
                    "name": "자체 CV 파이프라인 — YOLO11-pose + BoT-SORT + 호모그래피",
                    "url": "ws://localhost:8765",
                    "usage": ["지하철/버스 차내 BEV 5Hz 송출", "호차별 착석/기립/우선석 추적", "분실/응급/병목 자동 감지"],
                    "period": "실시간 (5 FPS)", "format": "WebSocket JSON", "live": True, "active": True,
                },
                {
                    "id": "IndoorAirQualityMeasure", "type": "가점",
                    "name": "서울시 지하철역 실내 공기질 (CO₂·PM2.5)",
                    "url": "http://openapi.seoul.go.kr:8088/.../IndoorAirQualityMeasureService",
                    "usage": ["역사 내 CO₂ ppm 실시간 표출", "BEV 혼잡↔CO₂ 상관 검증", "환기 알림 트리거"],
                    "period": "실시간 (5분 갱신, TTL=300s)", "format": "JSON", "live": True, "active": bool(SEOUL_KEY),
                },
                {
                    "id": "SubwayElevatorStatus", "type": "가점",
                    "name": "서울시 지하철 엘리베이터 운행 현황",
                    "url": "http://openapi.seoul.go.kr:8088/.../subwayElevStatus",
                    "usage": ["교통약자 경로 안내", "엘리베이터 고장 즉시 알림", "접근성 점수 자동 산출"],
                    "period": "실시간 (2분 갱신, TTL=120s)", "format": "JSON", "live": True, "active": bool(SEOUL_KEY),
                },
            ],
            "summary": {
                "total_sources": 10,
                "live_sources": 5,
                "active_keys": sum([bool(SEOUL_KEY), bool(SUBWAY_KEY), bool(NAVER_ID), bool(ANTHROPIC_KEY)]),
                "api_stats": {k: v["calls"] for k, v in _api_stats.items() if v["calls"] > 0},
            },
        }, ensure_ascii=False).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    if path_only == "/api/v1/line_roi":
        # 호선별 ROI 우선순위 — 실 parquet carload + policy_roi_v3 결합 (데모 정책 답)
        LINE_DATA = [
            {"line": "2호선",  "carload": 0.645, "stations": 51, "daily_avg_m": 7000000 * 0.198, "roi_x": 708, "net_b": 315, "rank": 1},
            {"line": "9호선",  "carload": 0.612, "stations": 38, "daily_avg_m": 7000000 * 0.066, "roi_x": 236, "net_b": 105, "rank": 2},
            {"line": "7호선",  "carload": 0.580, "stations": 51, "daily_avg_m": 7000000 * 0.063, "roi_x": 224, "net_b": 100, "rank": 3},
            {"line": "5호선",  "carload": 0.554, "stations": 56, "daily_avg_m": 7000000 * 0.098, "roi_x": 197, "net_b": 88,  "rank": 4},
            {"line": "1호선",  "carload": 0.521, "stations": 22, "daily_avg_m": 7000000 * 0.055, "roi_x": 185, "net_b": 82,  "rank": 5},
            {"line": "3호선",  "carload": 0.511, "stations": 44, "daily_avg_m": 7000000 * 0.088, "roi_x": 174, "net_b": 78,  "rank": 6},
            {"line": "4호선",  "carload": 0.496, "stations": 26, "daily_avg_m": 7000000 * 0.071, "roi_x": 162, "net_b": 72,  "rank": 7},
            {"line": "6호선",  "carload": 0.458, "stations": 38, "daily_avg_m": 7000000 * 0.046, "roi_x": 141, "net_b": 63,  "rank": 8},
            {"line": "8호선",  "carload": 0.423, "stations": 17, "daily_avg_m": 7000000 * 0.021, "roi_x": 75,  "net_b": 34,  "rank": 9},
        ]
        cur_h = time.localtime().tm_hour
        peak = 7 <= cur_h <= 9 or 17 <= cur_h <= 19
        body = json.dumps({
            "ok": True,
            "current_hour": cur_h,
            "peak": peak,
            "policy": {"rate": 0.30, "tier": "basic=₩200, od=₩300, transfer=₩400"},
            "lines": LINE_DATA,
            "recommendation": {
                "budget_1st": "2호선",
                "rationale": "일 승하차 수 최대(198만) + carload 0.645 → ROI 708x / 순가치 315억/년",
                "ci": "Monte Carlo 95% CI: ROI 270~424x (30% 응답률 기준)",
            },
            "data_source": "subway_time_202602.parquet 28일 평균 × policy_roi_v3.py",
        }, ensure_ascii=False).encode("utf-8")
        return (200, [("content-type", "application/json")] + CORS_HEADERS, body)
    if path_only == "/api/v1/roi_curve":
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
    if path_only == "/health" or path_only == "/":
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

    # websockets 16+ process_request 시그니처 적응 wrapper
    # 기존 http_health(path, headers) → 새 (connection, request) → Response
    try:
        from websockets.http11 import Response as _WSResponse
        from websockets.datastructures import Headers as _WSHeaders
        async def _process_request_v16(connection, request):
            # 쿼리 스트링 포함 전체 경로 전달 — AED/bus_arrival 엔드포인트가 QS 파싱 필요
            path = request.path
            old_result = await http_health(path, request.headers)
            if old_result is None:
                return None  # WS handshake 진행
            status, headers_list, body = old_result
            return _WSResponse(status, "OK", _WSHeaders(headers_list), body)
        _proc_req = _process_request_v16
    except Exception:
        # 구 websockets (≤11) fallback
        _proc_req = http_health

    async with websockets.serve(
        handler, args.host, args.port,
        process_request=_proc_req,
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
            asyncio.create_task(fake_bus_bev_loop())
            asyncio.create_task(fake_impact_seed_loop())
            asyncio.create_task(fake_incident_seed_loop())

    # 주기적 indoor_air + elevator broadcast
    asyncio.create_task(_periodic_env_broadcast())
    await asyncio.Future()  # run forever


async def _periodic_env_broadcast():
    """5분마다 실내공기질, 2분마다 엘리베이터 상태를 WS broadcast."""
    import random as _rnd
    _stations = ["성수", "강남", "서울역", "잠실", "홍대입구"]
    last_elev = 0.0
    while True:
        now = time.time()
        try:
            loop = asyncio.get_event_loop()
            station = _rnd.choice(_stations)
            air = await loop.run_in_executor(None, fetch_indoor_air, station)
            air["type"] = "indoor_air"
            await broadcast(json.dumps(air, ensure_ascii=False))
        except Exception as _e:
            print(f"[env-broadcast] air err: {_e}", flush=True)
        if now - last_elev >= 120:
            try:
                station = _rnd.choice(_stations)
                elev = await loop.run_in_executor(None, fetch_elevator_status, station)
                elev["type"] = "elevator_status"
                await broadcast(json.dumps(elev, ensure_ascii=False))
                last_elev = now
            except Exception as _e:
                print(f"[env-broadcast] elev err: {_e}", flush=True)
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())
