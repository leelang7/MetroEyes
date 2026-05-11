"""시민 앱 6종 모바일 스크린샷 자동 캡처 — outputs/demo/ 저장."""
from playwright.sync_api import sync_playwright
import pathlib, time

OUT = pathlib.Path(__file__).resolve().parent.parent / "outputs" / "demo"
OUT.mkdir(parents=True, exist_ok=True)

# GitHub Pages 기준 (로컬 파일도 동작)
BASE = "http://localhost:8787/frontend/passenger_app/index.html"

MOBILE = {"width": 390, "height": 844}  # iPhone 14 Pro 기준

def dismiss_modals(page):
    """팝업/모달 모두 닫기."""
    for _ in range(4):
        try:
            # OK 버튼
            btn = page.query_selector('button:has-text("OK"), button:has-text("확인"), button:has-text("닫기")')
            if btn:
                btn.click()
                page.wait_for_timeout(400)
                continue
        except Exception:
            pass
        # ESC
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception:
            pass
        break

def demo_time(page, hour: int = 18):
    """데모 시각 슬라이더를 hour 시로 맞춤."""
    try:
        page.evaluate(f"""
            const inp = document.querySelector('input[type=range]');
            if (inp) {{
                inp.value = {hour};
                inp.dispatchEvent(new Event('input', {{bubbles:true}}));
                inp.dispatchEvent(new Event('change', {{bubbles:true}}));
            }}
        """)
        page.wait_for_timeout(800)
    except Exception:
        pass

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport=MOBILE,
        device_scale_factor=2,
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
        is_mobile=True,
    )

    # ── 1. 지하철 메인 ─────────────────────────────────────────
    page = ctx.new_page()
    page.goto(BASE, timeout=20000, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    dismiss_modals(page)
    # 지하철 탭 확인 (기본)
    try:
        page.click('button:has-text("지하철")', timeout=2000)
    except Exception:
        pass
    demo_time(page, 18)
    dismiss_modals(page)
    page.wait_for_timeout(1000)
    page.screenshot(path=str(OUT / "citizen_subway_main.png"), full_page=False)
    print("OK citizen_subway_main.png")

    # ── 2. 지하철 칸 상세 + BEV (스크롤 다운) ────────────────────
    dismiss_modals(page)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.45)")
    page.wait_for_timeout(600)
    dismiss_modals(page)
    page.screenshot(path=str(OUT / "citizen_subway_detail.png"), full_page=False)
    print("OK citizen_subway_detail.png")
    page.close()

    # ── 3. 차내 뷰 (onboard) ─────────────────────────────────────
    ONBOARD = BASE.replace("index.html", "onboard.html") + "?demo=1"
    page = ctx.new_page()
    page.goto(ONBOARD, timeout=15000, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    dismiss_modals(page)
    demo_time(page, 18)
    dismiss_modals(page)
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "citizen_onboard_subway.png"), full_page=False)
    print("OK citizen_onboard_subway.png")
    page.close()

    # ── 4. 버스 메인 ─────────────────────────────────────────────
    page = ctx.new_page()
    page.goto(BASE, timeout=20000, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    dismiss_modals(page)
    try:
        page.click('button:has-text("버스")', timeout=3000)
        page.wait_for_timeout(1200)
    except Exception:
        pass
    demo_time(page, 18)
    dismiss_modals(page)
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "citizen_bus_main.png"), full_page=False)
    print("OK citizen_bus_main.png")

    # ── 5. 버스 칸 상세 (스크롤 다운) ────────────────────────────
    dismiss_modals(page)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.45)")
    page.wait_for_timeout(600)
    dismiss_modals(page)
    page.screenshot(path=str(OUT / "citizen_bus_detail.png"), full_page=False)
    print("OK citizen_bus_detail.png")
    page.close()

    # ── 6. 버스 차내 뷰 ──────────────────────────────────────────
    ONBOARD_BUS = BASE.replace("index.html", "onboard.html") + "?demo=1&mode=bus"
    page = ctx.new_page()
    page.goto(ONBOARD_BUS, timeout=15000, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    dismiss_modals(page)
    demo_time(page, 18)
    dismiss_modals(page)
    page.wait_for_timeout(800)
    page.screenshot(path=str(OUT / "citizen_bus_onboard.png"), full_page=False)
    print("OK citizen_bus_onboard.png")
    page.close()

    browser.close()

print(f"\n완료 → {OUT}")
for f in ["citizen_subway_main.png","citizen_subway_detail.png","citizen_onboard_subway.png",
          "citizen_bus_main.png","citizen_bus_detail.png","citizen_bus_onboard.png"]:
    fp = OUT / f
    status = f"{fp.stat().st_size//1024}KB" if fp.exists() else "MISSING"
    print(f"  {f}: {status}")
