// MetroEyes 백엔드 health pill — 운영자 4페이지 공용
// 사용법: HTML 어디든 <span id="health-pill"></span> + <script src="../shared/health_pill.js" defer></script>
// /health 8초 폴링하여 CV fps / API 오류율 / 클라이언트 수 압축 표시
(function () {
  const PILL_ID = 'health-pill';
  const POLL_MS = 8000;

  function deriveHealthURL() {
    // 페이지 host 기반 기본 도출. window.LIVE_WS_URL 가 있으면 그쪽으로.
    const wsUrl = window.LIVE_WS_URL || (
      location.protocol === 'https:'
        ? `wss://${location.host}`
        : `ws://localhost:8765`
    );
    return wsUrl.replace(/^wss:\/\//, 'https://').replace(/^ws:\/\//, 'http://') + '/health';
  }

  function ensurePill() {
    let el = document.getElementById(PILL_ID);
    if (!el) {
      el = document.createElement('span');
      el.id = PILL_ID;
      el.style.cssText = 'display:none; padding:3px 9px; border-radius:999px; font-size:11px; font-weight:700; letter-spacing:.3px; font-feature-settings:"tnum"; margin-left:8px; cursor:help;';
      el.title = '백엔드 라이브 상태 (8초 폴링)';
      // 기본: header 안에 자동 삽입
      const header = document.querySelector('header .controls') || document.querySelector('header');
      if (header) header.appendChild(el);
    }
    return el;
  }

  async function poll() {
    const el = ensurePill();
    if (!el) return;
    try {
      const r = await fetch(deriveHealthURL(), { cache: 'no-cache', mode: 'cors' });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      // 종합 점수: CV active + API 오류율 < 30%
      const cv = j.cv;
      const api = j.api || {};
      const apiVals = Object.values(api);
      const totalCalls = apiVals.reduce((a, b) => a + b.calls, 0);
      const totalErrors = apiVals.reduce((a, b) => a + b.errors, 0);
      const errRate = totalCalls ? totalErrors / totalCalls : 0;
      const cvActive = cv && (Date.now() / 1000 - cv.last_ts < 10);
      let badge, color, text;
      if (cvActive && errRate < 0.10) {
        color = '#10b981'; badge = '🟢 백엔드 OK';
      } else if (cvActive || errRate < 0.30) {
        color = '#f59e0b'; badge = '🟡 부분 가용';
      } else {
        color = '#ef4444'; badge = '🔴 점검 필요';
      }
      const fpsTxt = cv ? ` · ${cv.fps} fps` : '';
      const errTxt = totalCalls ? ` · ${(errRate*100).toFixed(0)}% err` : '';
      const cliTxt = j.clients != null ? ` · ${j.clients} ws` : '';
      el.textContent = badge + fpsTxt + errTxt + cliTxt;
      el.style.background = `rgba(${color === '#10b981' ? '16,185,129' : color === '#f59e0b' ? '245,158,11' : '239,68,68'}, .14)`;
      el.style.border = `1px solid ${color}`;
      el.style.color = color;
      el.style.display = 'inline-block';
      el.title = [
        cv ? `CV: ${cv.fps} fps · ${cv.tracks} 트랙 · ${cv.demo ? 'demo 모드' : '실 CV'}` : 'CV 미실행',
        totalCalls ? `API ${totalCalls}회 · 오류 ${totalErrors}건 (${(errRate*100).toFixed(1)}%)` : 'API 호출 없음',
        `WebSocket 클라이언트 ${j.clients}`,
      ].join('\n');
    } catch (e) {
      el.textContent = '⚫ 백엔드 끊김';
      el.style.background = 'rgba(107,118,138,.12)';
      el.style.border = '1px solid #6b768a';
      el.style.color = '#6b768a';
      el.style.display = 'inline-block';
      el.title = 'fetch /health 실패 — backend 가 실행 중인지 확인하세요.';
    }
  }
  poll();
  setInterval(poll, POLL_MS);
})();
