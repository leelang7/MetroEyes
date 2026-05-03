"""MetroEyes 데모 캡처 — 화면별 PNG/영상 자동 생성.

Playwright(Chromium)로 운영자/시민 화면 캡처.
backend가 살아있으면 라이브 데이터, 죽어있으면 시뮬 fallback 그대로.

설치 (한 번):
    pip install playwright
    playwright install chromium

실행:
    python scripts/capture_demo.py                   # PNG 3장
    python scripts/capture_demo.py --record          # + 운영자 30초 webm
    python scripts/capture_demo.py --ws ws://...     # 백엔드 URL override

산출:
    outputs/demo/
      operator_realbev.png
      operator_index.png
      citizen_pwa.png
      operator_realbev.webm  (--record 시)
"""
from __future__ import annotations

import argparse
import asyncio
import http.server
import socketserver
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs" / "demo"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PORT = 5173  # local static server


def _start_static_server() -> threading.Thread:
    handler = http.server.SimpleHTTPRequestHandler

    class _ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    httpd = _ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    print(f"[http] static server on http://127.0.0.1:{PORT}", flush=True)
    return th


async def capture_page(context, url: str, png_out: Path,
                        wait_ms: int = 4000, viewport=(1440, 900),
                        full_page: bool = False) -> None:
    page = await context.new_page()
    await page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    print(f"[goto] {url}", flush=True)
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(wait_ms)
    await page.screenshot(path=str(png_out), full_page=full_page)
    print(f"[png ] {png_out.relative_to(ROOT)}", flush=True)
    await page.close()


async def record_clip(context, url: str, seconds: int, viewport=(1440, 900)) -> None:
    """30초 화면 녹화 (webm)."""
    page = await context.new_page()
    await page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    await page.goto(url, wait_until="domcontentloaded")
    print(f"[rec ] {url} for {seconds}s ...", flush=True)
    await page.wait_for_timeout(seconds * 1000)
    await page.close()


async def main(args) -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        sys.exit("playwright 미설치.\n  pip install playwright\n  playwright install chromium")

    _start_static_server()
    base = f"http://127.0.0.1:{PORT}"
    qs = f"?ws={args.ws}" if args.ws else ""

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx_kwargs = {}
        if args.record:
            ctx_kwargs["record_video_dir"] = str(OUT_DIR)
            ctx_kwargs["record_video_size"] = {"width": 1440, "height": 900}
        ctx = await browser.new_context(**ctx_kwargs)

        # 운영자 realbev: 카드 많아서 긴 viewport + 풀페이지 + 모든 라이브 데이터 도착까지 대기
        await capture_page(ctx, f"{base}/frontend/operator_web/realbev.html{qs}",
                            OUT_DIR / "operator_realbev.png", wait_ms=12000,
                            viewport=(1600, 1400), full_page=True)
        await capture_page(ctx, f"{base}/frontend/operator_web/index.html{qs}",
                            OUT_DIR / "operator_index.png", wait_ms=8000,
                            viewport=(1600, 1100), full_page=True)
        await capture_page(ctx, f"{base}/frontend/operator_web/bus.html{qs}",
                            OUT_DIR / "operator_bus.png", wait_ms=8000,
                            viewport=(1600, 1100), full_page=True)
        await capture_page(ctx, f"{base}/frontend/passenger_app/index.html{qs}",
                            OUT_DIR / "citizen_pwa.png", wait_ms=10000,
                            viewport=(440, 1100), full_page=True)

        if args.record:
            await record_clip(ctx, f"{base}/frontend/operator_web/realbev.html{qs}",
                                seconds=args.record_seconds)

        await ctx.close()
        await browser.close()

    if args.record:
        # webm 파일명을 사람 친화로 정리
        for w in OUT_DIR.glob("*.webm"):
            target = OUT_DIR / "operator_realbev.webm"
            try: w.rename(target)
            except OSError: pass

    print()
    print(f"[done] 산출물 → {OUT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ws", default=None, help="백엔드 WS URL override")
    parser.add_argument("--record", action="store_true", help="운영자 화면 webm 녹화")
    parser.add_argument("--record-seconds", type=int, default=30)
    asyncio.run(main(parser.parse_args()))
