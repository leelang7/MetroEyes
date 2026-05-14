// MetroEyes 시연 오버레이 — realbev / bus / operator subway 공통
// 처음 보는 사람도 한 눈에 알 수 있는 임팩트 시각화:
//   ① 상단 큰 시간 배너 (48px hour + phase 라벨, 양봉 피크 진입 시 색상/펄스)
//   ② 진행률 프로그레스 바
//   ③ 사고 발생 시 화면 중앙 BIG TOAST (4초, 아이콘 + 색상 + 글로우)
//   ④ 종료 시 결과 요약 토스트
// 사용:
//   DemoOverlay.runScenario({
//     duration: 30000,
//     events: [{ at: 8000, type: 'emergency', sev: 'high', icon: '🚨', color: '#ff5e57', label: '응급 검출', msg: '...' }, ...],
//     onSendIncident: (ev) => ws.send(...),
//     onSetHour: (h) => MLChart.setDemoHour(h),
//   });
(function () {
  if (window.DemoOverlay) return;
  let active = false;
  let cssInjected = false;

  function injectCSS() {
    if (cssInjected) return; cssInjected = true;
    const s = document.createElement('style');
    s.textContent = `
      .demo-banner {
        position: fixed; top: 70px; left: 50%; transform: translateX(-50%);
        background: linear-gradient(135deg, rgba(8,12,20,.95), rgba(20,20,30,.92));
        backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(125,211,211,.30);
        border-radius: 16px; padding: 14px 22px;
        z-index: 9998; box-shadow: 0 16px 50px rgba(0,0,0,.6), 0 0 60px rgba(125,211,211,.15);
        display: flex; align-items: center; gap: 18px;
        animation: dbanner-in .4s cubic-bezier(.22,.61,.36,1);
      }
      .demo-banner.peak-am { border-color: rgba(125,211,211,.65); box-shadow: 0 16px 50px rgba(0,0,0,.6), 0 0 60px rgba(125,211,211,.45); }
      .demo-banner.peak-pm { border-color: rgba(245,158,11,.65); box-shadow: 0 16px 50px rgba(0,0,0,.6), 0 0 60px rgba(245,158,11,.45); }
      @keyframes dbanner-in { from { opacity: 0; transform: translateX(-50%) translateY(-12px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
      .demo-banner .db-clock {
        font: 700 44px/1.0 ui-monospace, Consolas, monospace;
        color: #fff; letter-spacing: -1px;
        text-shadow: 0 0 22px currentColor;
      }
      .demo-banner.peak-am .db-clock { color: #7dd3d3; }
      .demo-banner.peak-pm .db-clock { color: #f59e0b; }
      .demo-banner .db-phase {
        display: flex; flex-direction: column; gap: 3px; min-width: 160px;
      }
      .demo-banner .db-phase b { font-size: 14px; color: #fff; font-weight: 700; letter-spacing: -.2px; }
      .demo-banner .db-phase span { font-size: 10px; color: #8a8a96; letter-spacing: 1.3px; text-transform: uppercase; }
      .demo-banner .db-prog-wrap {
        width: 200px; height: 6px; background: rgba(255,255,255,.08); border-radius: 99px; overflow: hidden;
      }
      .demo-banner .db-prog {
        height: 100%; width: 0; background: linear-gradient(90deg, #7dd3d3, #f59e0b, #ef4444);
        transition: width .25s linear;
      }
      .demo-banner .db-count {
        font: 700 22px/1 ui-monospace, monospace; color: #fff;
        font-variant-numeric: tabular-nums; padding-left: 14px;
        border-left: 1px solid rgba(255,255,255,.12);
      }
      .demo-banner .db-count small { display: block; font: 500 10px ui-monospace, monospace; color: #8a8a96; letter-spacing: 1.2px; margin-top: 4px; text-transform: uppercase; }

      .demo-big-toast {
        position: fixed; top: 48%; left: 50%; transform: translate(-50%, -50%) scale(.85);
        background: rgba(15,17,24,.95);
        backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
        border: 2px solid var(--dbt-color, #7dd3d3);
        border-radius: 24px; padding: 26px 38px;
        z-index: 9999; min-width: 460px; max-width: 720px;
        box-shadow: 0 30px 90px rgba(0,0,0,.7), 0 0 90px var(--dbt-glow, rgba(125,211,211,.35));
        opacity: 0;
        animation: dbtoast-in .35s cubic-bezier(.22,.61,.36,1) forwards;
        display: flex; align-items: center; gap: 22px;
      }
      @keyframes dbtoast-in {
        0% { opacity: 0; transform: translate(-50%, -50%) scale(.7); }
        70% { opacity: 1; transform: translate(-50%, -50%) scale(1.04); }
        100% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
      }
      .demo-big-toast.out { animation: dbtoast-out .3s ease-in forwards; }
      @keyframes dbtoast-out {
        from { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        to { opacity: 0; transform: translate(-50%, -50%) scale(.85); }
      }
      .demo-big-toast .dbt-icon {
        font-size: 56px; line-height: 1;
        filter: drop-shadow(0 0 18px var(--dbt-glow, rgba(125,211,211,.4)));
      }
      .demo-big-toast .dbt-body { flex: 1; min-width: 0; }
      .demo-big-toast .dbt-label {
        font: 700 11px/1 ui-monospace, monospace; color: var(--dbt-color, #7dd3d3);
        letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px;
      }
      .demo-big-toast .dbt-msg {
        font: 600 19px/1.4 -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", sans-serif;
        color: #fff; letter-spacing: -.3px;
      }
      .demo-big-toast .dbt-meta {
        font: 500 11px/1 ui-monospace, monospace; color: #8a8a96;
        margin-top: 8px; letter-spacing: .8px;
      }

      /* 피크 페이즈 화면 가장자리 글로우 */
      .demo-page-glow::before {
        content: ''; position: fixed; inset: 0; pointer-events: none; z-index: 9990;
        box-shadow: inset 0 0 120px var(--page-glow, rgba(125,211,211,.18));
        animation: dpage-pulse 2.4s ease-in-out infinite;
      }
      @keyframes dpage-pulse { 0%, 100% { opacity: 1; } 50% { opacity: .55; } }
    `;
    document.head.appendChild(s);
  }

  let banner = null;
  function showBanner() {
    if (banner) return;
    banner = document.createElement('div');
    banner.className = 'demo-banner';
    banner.innerHTML = `
      <div class="db-clock" id="dbn-clock">00:00</div>
      <div class="db-phase">
        <b id="dbn-phase">시연 시작</b>
        <span id="dbn-phase-sub">양봉 패턴 시뮬</span>
      </div>
      <div class="db-prog-wrap"><div class="db-prog" id="dbn-prog"></div></div>
      <div class="db-count"><span id="dbn-count">0</span><small>이벤트 검출</small></div>
    `;
    document.body.appendChild(banner);
  }
  function hideBanner() {
    if (!banner) return;
    banner.style.animation = 'dbanner-in .25s reverse';
    setTimeout(() => { banner?.remove(); banner = null; }, 250);
  }
  function setBannerHour(h, phase, peak) {
    if (!banner) return;
    const hh = String(h).padStart(2, '0');
    const min = String(Math.floor(Math.random() * 60)).padStart(2, '0');
    document.getElementById('dbn-clock').textContent = `${hh}:${min}`;
    document.getElementById('dbn-phase').textContent = phase;
    document.getElementById('dbn-phase-sub').textContent = peak === 'am' ? '출근 시간대 피크' : peak === 'pm' ? '퇴근 시간대 피크' : '평상 시간대';
    banner.classList.toggle('peak-am', peak === 'am');
    banner.classList.toggle('peak-pm', peak === 'pm');
    // 페이지 글로우
    if (peak === 'am') document.documentElement.style.setProperty('--page-glow', 'rgba(125,211,211,.22)');
    else if (peak === 'pm') document.documentElement.style.setProperty('--page-glow', 'rgba(245,158,11,.22)');
    document.body.classList.toggle('demo-page-glow', !!peak);
  }
  function setBannerProgress(pct, count) {
    if (!banner) return;
    document.getElementById('dbn-prog').style.width = pct + '%';
    if (count != null) document.getElementById('dbn-count').textContent = count;
  }

  function bigToast({ icon = '✦', label = '검출', msg = '', meta = '', color = '#7dd3d3', glow = 'rgba(125,211,211,.4)', life = 3600 }) {
    const t = document.createElement('div');
    t.className = 'demo-big-toast';
    t.style.setProperty('--dbt-color', color);
    t.style.setProperty('--dbt-glow', glow);
    t.innerHTML = `
      <div class="dbt-icon">${icon}</div>
      <div class="dbt-body">
        <div class="dbt-label">${label}</div>
        <div class="dbt-msg">${msg}</div>
        ${meta ? `<div class="dbt-meta">${meta}</div>` : ''}
      </div>
    `;
    document.body.appendChild(t);
    setTimeout(() => { t.classList.add('out'); setTimeout(() => t.remove(), 300); }, life);
  }

  function phaseFor(h) {
    if (h >= 7 && h <= 9) return { name: '🌅 출근 피크', peak: 'am' };
    if (h >= 17 && h <= 19) return { name: '🌆 퇴근 피크', peak: 'pm' };
    if (h >= 10 && h <= 16) return { name: '🌞 평상 시간', peak: null };
    if (h >= 20 && h <= 23) return { name: '🌙 야간', peak: null };
    return { name: '🌌 새벽', peak: null };
  }

  async function runScenario({ duration = 30000, events = [], onSendIncident, onSetHour }) {
    if (active) return; active = true;
    injectCSS();
    showBanner();
    const t0 = Date.now();
    let evCount = 0;

    const hourT = setInterval(() => {
      const dt = Date.now() - t0;
      const h = Math.min(23, Math.floor(dt / duration * 24));
      const ph = phaseFor(h);
      setBannerHour(h, ph.name, ph.peak);
      setBannerProgress(Math.min(100, dt / duration * 100), evCount);
      try { onSetHour?.(h); } catch {}
      if (dt >= duration) clearInterval(hourT);
    }, 250);

    events.forEach((e) => {
      setTimeout(() => {
        bigToast(e);
        evCount++;
        setBannerProgress(Math.min(100, (Date.now() - t0) / duration * 100), evCount);
        try { onSendIncident?.(e); } catch {}
      }, e.at);
    });

    setTimeout(() => {
      hideBanner();
      document.body.classList.remove('demo-page-glow');
      bigToast({
        icon: '✓', label: '시연 종료', color: '#10b981', glow: 'rgba(16,185,129,.4)',
        msg: `30초 양봉 시뮬레이션 완료 — ${evCount}건 사고 검출`,
        meta: '응급 / 분실 / 무임 / 이상 / 분산 — 자동 분류 + 백엔드 동기화',
        life: 4500,
      });
      active = false;
    }, duration);
  }

  window.DemoOverlay = { runScenario, bigToast };
})();
