"""성수 시나리오 — arrival + population + citydata 동시 실호출 검증."""
import asyncio, json
import websockets

URL = "ws://localhost:8765"

async def call(ws, msg, label):
    await ws.send(json.dumps(msg))
    try:
        for _ in range(3):
            r = await asyncio.wait_for(ws.recv(), timeout=6)
            j = json.loads(r)
            t = j.get('type', 'unknown')
            # BEV frame skip
            if 'tracks' in j:
                continue
            print(f"\n[{label}] type={t}")
            for k, v in j.items():
                if k == 'tracks': continue
                s = str(v)
                if len(s) > 90: s = s[:90] + '...'
                print(f"  {k}: {s}")
            return
    except asyncio.TimeoutError:
        print(f"[{label}] TIMEOUT (no response)")

async def main():
    async with websockets.connect(URL) as ws:
        await call(ws, {'type':'arrival_query','stationName':'성수','line':2}, 'ARRIVAL 성수')
        await call(ws, {'type':'population_query','poi':'성수카페거리'}, 'POPULATION 성수카페거리')
        await call(ws, {'type':'arrival_query','stationName':'잠실','line':2}, 'ARRIVAL 잠실 (대조)')
        await call(ws, {'type':'population_query','poi':'잠실역'}, 'POPULATION 잠실역 (대조)')

asyncio.run(main())
