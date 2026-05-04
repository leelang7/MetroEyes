"""실 ws 호출 검증 — population_query(성수카페거리) 보내고 응답 출력."""
import asyncio
import json
import sys

import websockets

URL = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765"
POI = sys.argv[2] if len(sys.argv) > 2 else "성수카페거리"

async def main():
    print(f"[probe] connecting {URL} ...", flush=True)
    async with websockets.connect(URL, open_timeout=5, close_timeout=2) as ws:
        print(f"[probe] connected. sending population_query(poi={POI})", flush=True)
        await ws.send(json.dumps({"type": "population_query", "poi": POI}))
        try:
            for _ in range(3):  # 응답 + 폭증이면 추가 context 까지 최대 3개
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                j = json.loads(msg)
                t = j.get("type")
                if t == "population":
                    print(f"\n[POPULATION] poi={j.get('poi')} area={j.get('area_nm')}")
                    print(f"  congest_lvl: {j.get('congest_lvl')}")
                    print(f"  ppltn:       {j.get('ppltn_min')} ~ {j.get('ppltn_max')} 명")
                    print(f"  msg:         {(j.get('congest_msg') or '')[:80]}")
                    print(f"  time:        {j.get('ppltn_time')}")
                    if j.get('error'):
                        print(f"  ERROR:       {j['error']}")
                elif t == "context":
                    print(f"\n[CONTEXT — 폭증 감지 → 네이버+Claude 자동 broadcast]")
                    print(f"  trigger: {j.get('trigger')}")
                    print(f"  summary: {j.get('summary')}")
                    print(f"  sources: {j.get('sources')}")
                    for n in (j.get('news') or [])[:3]:
                        print(f"   - {n.get('title')[:70]}")
                else:
                    print(f"\n[{t}] {str(j)[:200]}")
        except asyncio.TimeoutError:
            print("[probe] no more messages (timeout 8s).")

asyncio.run(main())
