// MetroEyes 시연 오버레이 — realbev / bus / operator subway 공통
// 인라인 스타일 + max z-index로 페이지별 CSS 충돌 차단
(function () {
  if (window.DemoOverlay) return;
  let active = false;
  let pulseInjected = false;

  // pulse 키프레임만 stylesheet로 (인라인 불가)
  function injectPulse() {
    if (pulseInjected) return; pulseInjected = true;
    const s = document.createElement('style');
    s.textContent = `
      @keyframes dbanner-in { from { opacity: 0; transform: translateX(-50%) translateY(-12px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
      @keyframes dbtoast-in { 0% { opacity: 0; transform: translate(-50%, -50%) scale(.7); } 70% { opacity: 1; transform: translate(-50%, -50%) scale(1.04); } 100% { opacity: 1; transform: translate(-50%, -50%) scale(1); } }
      @keyframes dbtoast-out { from { opacity: 1; transform: translate(-50%, -50%) scale(1); } to { opacity: 0; transform: translate(-50%, -50%) scale(.85); } }
      @keyframes dpage-pulse { 0%, 100% { opacity: 1; } 50% { opacity: .55; } }
    `;
    document.head.appendChild(s);
  }

  let banner = null;
  let clockEl, phaseEl, phaseSubEl, progEl, countEl;

  function showBanner() {
    injectPulse();
    if (banner) return;
    banner = document.createElement('div');
    banner.id = 'demo-overlay-banner';
    banner.style.cssText = [
      'position: fixed', 'top: 80px', 'left: 50%', 'transform: translateX(-50%)',
      'background: linear-gradient(135deg, rgba(8,12,20,.95), rgba(20,20,30,.92))',
      'backdrop-filter: blur(14px)', '-webkit-backdrop-filter: blur(14px)',
      'border: 2px solid rgba(125,211,211,.45)',
      'border-radius: 16px', 'padding: 14px 22px',
      'z-index: 2147483646',
      'box-shadow: 0 16px 50px rgba(0,0,0,.7), 0 0 70px rgba(125,211,211,.30)',
      'display: flex', 'align-items: center', 'gap: 18px',
      'animation: dbanner-in .4s cubic-bezier(.22,.61,.36,1)',
      'pointer-events: none',
      'font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", sans-serif',
    ].join(';');
    banner.innerHTML = `
      <div id="dbn-clock" style="font: 700 44px/1.0 ui-monospace, Consolas, monospace; color: #7dd3d3; letter-spacing: -1px; text-shadow: 0 0 22px currentColor;">00:00</div>
      <div style="display: flex; flex-direction: column; gap: 3px; min-width: 160px;">
        <b id="dbn-phase" style="font-size: 14px; color: #fff; font-weight: 700; letter-spacing: -.2px;">시연 시작</b>
        <span id="dbn-phase-sub" style="font-size: 10px; color: #8a8a96; letter-spacing: 1.3px; text-transform: uppercase;">양봉 패턴 시뮬</span>
      </div>
      <div style="width: 200px; height: 6px; background: rgba(255,255,255,.08); border-radius: 99px; overflow: hidden;">
        <div id="dbn-prog" style="height: 100%; width: 0; background: linear-gradient(90deg, #7dd3d3, #f59e0b, #ef4444); transition: width .25s linear;"></div>
      </div>
      <div style="font: 700 22px/1 ui-monospace, monospace; color: #fff; font-variant-numeric: tabular-nums; padding-left: 14px; border-left: 1px solid rgba(255,255,255,.12);">
        <span id="dbn-count">0</span>
        <small style="display: block; font: 500 10px ui-monospace, monospace; color: #8a8a96; letter-spacing: 1.2px; margin-top: 4px; text-transform: uppercase;">이벤트 검출</small>
      </div>
    `;
    document.body.appendChild(banner);
    clockEl = banner.querySelector('#dbn-clock');
    phaseEl = banner.querySelector('#dbn-phase');
    phaseSubEl = banner.querySelector('#dbn-phase-sub');
    progEl = banner.querySelector('#dbn-prog');
    countEl = banner.querySelector('#dbn-count');
  }

  function hideBanner() {
    if (!banner) return;
    banner.style.opacity = '0';
    banner.style.transition = 'opacity .3s ease';
    setTimeout(() => { banner?.remove(); banner = null; }, 320);
    document.body.style.boxShadow = '';
  }

  function setBannerHour(h, phase, peak) {
    if (!banner) return;
    const hh = String(h).padStart(2, '0');
    const min = String(Math.floor(Math.random() * 60)).padStart(2, '0');
    clockEl.textContent = `${hh}:${min}`;
    phaseEl.textContent = phase;
    phaseSubEl.textContent = peak === 'am' ? '출근 시간대 피크' : peak === 'pm' ? '퇴근 시간대 피크' : '평상 시간대';
    if (peak === 'am') {
      clockEl.style.color = '#7dd3d3';
      banner.style.borderColor = 'rgba(125,211,211,.65)';
      banner.style.boxShadow = '0 16px 50px rgba(0,0,0,.7), 0 0 90px rgba(125,211,211,.55)';
    } else if (peak === 'pm') {
      clockEl.style.color = '#f59e0b';
      banner.style.borderColor = 'rgba(245,158,11,.65)';
      banner.style.boxShadow = '0 16px 50px rgba(0,0,0,.7), 0 0 90px rgba(245,158,11,.55)';
    } else {
      clockEl.style.color = '#7dd3d3';
      banner.style.borderColor = 'rgba(125,211,211,.45)';
      banner.style.boxShadow = '0 16px 50px rgba(0,0,0,.7), 0 0 70px rgba(125,211,211,.30)';
    }
  }
  function setBannerProgress(pct, count) {
    if (!banner) return;
    progEl.style.width = pct + '%';
    if (count != null) countEl.textContent = count;
  }

  function bigToast({ icon = '✦', label = '검출', msg = '', meta = '', color = '#7dd3d3', glow = 'rgba(125,211,211,.4)', life = 3600 }) {
    injectPulse();
    const t = document.createElement('div');
    t.style.cssText = [
      'position: fixed', 'top: 48%', 'left: 50%',
      'background: rgba(15,17,24,.96)',
      'backdrop-filter: blur(20px)', '-webkit-backdrop-filter: blur(20px)',
      `border: 2px solid ${color}`,
      'border-radius: 24px', 'padding: 26px 38px',
      'z-index: 2147483647',
      'min-width: 460px', 'max-width: 720px',
      `box-shadow: 0 30px 90px rgba(0,0,0,.75), 0 0 90px ${glow}`,
      'opacity: 0',
      'animation: dbtoast-in .35s cubic-bezier(.22,.61,.36,1) forwards',
      'display: flex', 'align-items: center', 'gap: 22px',
      'pointer-events: none',
      'transform: translate(-50%, -50%)',
      'font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", sans-serif',
    ].join(';');
    t.innerHTML = `
      <div style="font-size: 56px; line-height: 1; filter: drop-shadow(0 0 18px ${glow});">${icon}</div>
      <div style="flex: 1; min-width: 0;">
        <div style="font: 700 11px/1 ui-monospace, monospace; color: ${color}; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px;">${label}</div>
        <div style="font: 600 19px/1.4 -apple-system, BlinkMacSystemFont, 'Pretendard', 'Segoe UI', sans-serif; color: #fff; letter-spacing: -.3px;">${msg}</div>
        ${meta ? `<div style="font: 500 11px/1 ui-monospace, monospace; color: #8a8a96; margin-top: 8px; letter-spacing: .8px;">${meta}</div>` : ''}
      </div>
    `;
    document.body.appendChild(t);
    setTimeout(() => {
      t.style.animation = 'dbtoast-out .3s ease-in forwards';
      setTimeout(() => t.remove(), 320);
    }, life);
  }

  function phaseFor(h) {
    if (h >= 7 && h <= 9) return { name: '🌅 출근 피크', peak: 'am' };
    if (h >= 17 && h <= 19) return { name: '🌆 퇴근 피크', peak: 'pm' };
    if (h >= 10 && h <= 16) return { name: '🌞 평상 시간', peak: null };
    if (h >= 20 && h <= 23) return { name: '🌙 야간', peak: null };
    return { name: '🌌 새벽', peak: null };
  }

  function runScenario({ duration = 30000, events = [], onSendIncident, onSetHour }) {
    if (active) { console.warn('[DemoOverlay] 이미 실행 중'); return; }
    active = true;
    try {
      console.log('[DemoOverlay] runScenario 시작 — duration:', duration, '이벤트:', events.length);
      showBanner();
    } catch (e) {
      console.error('[DemoOverlay] showBanner 실패:', e);
      active = false;
      return;
    }
    const t0 = Date.now();
    let evCount = 0;

    const hourT = setInterval(() => {
      const dt = Date.now() - t0;
      const h = Math.min(23, Math.floor(dt / duration * 24));
      const ph = phaseFor(h);
      try { setBannerHour(h, ph.name, ph.peak); } catch (e) { console.error('[DemoOverlay] setBannerHour:', e); }
      setBannerProgress(Math.min(100, dt / duration * 100), evCount);
      try { onSetHour?.(h); } catch {}
      if (dt >= duration) clearInterval(hourT);
    }, 250);

    events.forEach((e) => {
      setTimeout(() => {
        try { bigToast(e); }
        catch (err) { console.error('[DemoOverlay] bigToast 실패:', err); }
        evCount++;
        setBannerProgress(Math.min(100, (Date.now() - t0) / duration * 100), evCount);
        try { onSendIncident?.(e); } catch (err) { console.error('[DemoOverlay] onSendIncident:', err); }
      }, e.at);
    });

    setTimeout(() => {
      hideBanner();
      bigToast({
        icon: '✓', label: '시연 종료', color: '#10b981', glow: 'rgba(16,185,129,.4)',
        msg: `30초 양봉 시뮬레이션 완료 — ${evCount}건 사고 검출`,
        meta: '응급 / 분실 / 무임 / 이상 / 분산 — 자동 분류 + 백엔드 동기화',
        life: 4500,
      });
      active = false;
      console.log('[DemoOverlay] 종료');
    }, duration);
  }

  window.DemoOverlay = { runScenario, bigToast };
  console.log('[DemoOverlay] ready');
})();
