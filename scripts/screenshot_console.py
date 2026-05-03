"""운영자 콘솔 PoC를 headless Chromium 으로 렌더링하여 PNG로 저장.

산출: outputs/figs/console_h{HH}.png  (시간 슬라이더 다른 값 3장)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / "frontend" / "operator_web" / "index.html").resolve().as_uri()
OUT = ROOT / "outputs" / "figs"
OUT.mkdir(parents=True, exist_ok=True)

from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 850}, device_scale_factor=2)
        page = ctx.new_page()
        page.goto(HTML)
        page.wait_for_load_state("networkidle")
        for hour in (8, 13, 18):
            page.evaluate(
                """(h) => {
                    const el = document.getElementById('hour');
                    el.value = String(h);
                    el.dispatchEvent(new Event('input'));
                    // sim 사이클 강제로 'stopped' (출입문 활성, 흐름 화살표 표시)
                    if (window.sim) {
                      window.sim.cyclePhase = 'stopped';
                      window.sim.cycleT = 2;
                      window.sim.doorActiveAlpha = 1;
                    }
                }""",
                hour,
            )
            # 시뮬레이션이 사람 위치를 정착시킬 시간 (브라운 운동 + 좌석 정착)
            page.wait_for_timeout(1800)
            out = OUT / f"console_h{hour:02d}.png"
            page.screenshot(path=str(out), full_page=False)
            print(f"saved → {out.relative_to(ROOT)}")
        browser.close()


if __name__ == "__main__":
    main()
