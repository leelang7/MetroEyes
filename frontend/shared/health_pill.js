// MetroEyes 백엔드 health pill — window.LIVE_WS readyState 기반 (운영자 4페이지 공용)
// 사용법: HTML 어디든 <span id="health-pill"></span> + <script src="../shared/health_pill.js" defer></script>
(function () {
  const PILL_ID = 'health-pill';
  const POLL_MS = 2000;

  function ensurePill() {
    let el = document.getElementById(PILL_ID);
    if (!el) {
      el = document.createElement('span');
      el.id = PILL_ID;
      el.style.cssText = 'display:inline-block; padding:3px 9px; border-radius:999px; font-size:11px; font-weight:700; letter-spacing:.3px; margin-left:8px; cursor:default;';
      const header = document.querySelector('header .controls') || document.querySelector('header');
      if (header) header.appendChild(el);
    }
    return el;
  }

  function poll() {
    const el = ensurePill();
    if (!el) return;
    const ws = window.LIVE_WS || window.ws || window._ws;
    const connected = ws && ws.readyState === 1; // WebSocket.OPEN
    if (connected) {
      el.textContent = '🟢 연결됨';
      el.style.background = 'rgba(16,185,129,.14)';
      el.style.border = '1px solid #10b981';
      el.style.color = '#10b981';
    } else {
      el.textContent = '⚫ 끊김';
      el.style.background = 'rgba(107,118,138,.12)';
      el.style.border = '1px solid #6b768a';
      el.style.color = '#6b768a';
    }
  }

  poll();
  setInterval(poll, POLL_MS);
})();
