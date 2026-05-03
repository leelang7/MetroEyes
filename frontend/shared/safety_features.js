// 안전 감지 + TTS 다국어 + 약자 모드 헬퍼
// 운영자 콘솔과 시민 앱에서 공통으로 쓰는 작은 유틸들.

(function (global) {
  'use strict';

  const TYPE_LABEL = {
    emergency: '응급',
    suspicious: '이상행동',
    lost: '분실물',
    free_ride: '무임승차',
  };
  const TYPE_ICON = {
    emergency: '🚨',
    suspicious: '⚠',
    lost: '🎒',
    free_ride: '⊘',
  };

  function formatRelTime(ts) {
    const diff = Math.max(0, Math.floor((performance.now() - ts) / 1000));
    if (diff < 5) return '방금';
    if (diff < 60) return `${diff}초 전`;
    return `${Math.floor(diff / 60)}분 전`;
  }

  // ============== TTS ==============
  // 다국어 안내 메시지 — 운영자 콘솔의 분산 안내 송출용
  const TTS_TEMPLATES = {
    'ko': {
      lang: 'ko-KR',
      crowded: (carLabel, recCar) => `${carLabel} 혼잡합니다. ${recCar}으로 분산해주세요.`,
      emergency: (carLabel) => `${carLabel}에서 응급 환자가 감지되었습니다. 승무원이 확인 중입니다.`,
      lost: (carLabel) => `${carLabel}에서 잔존 물품이 감지되었습니다.`,
      arrival: (carLabel, occ) => `다음 ${carLabel} 점유율 ${occ}퍼센트입니다.`,
    },
    'en': {
      lang: 'en-US',
      crowded: (carLabel, recCar) => `${carLabel} is crowded. Please move to ${recCar}.`,
      emergency: (carLabel) => `Medical emergency detected in ${carLabel}. Crew is being notified.`,
      lost: (carLabel) => `Unattended item detected in ${carLabel}.`,
      arrival: (carLabel, occ) => `${carLabel} is at ${occ} percent occupancy.`,
    },
    'zh': {
      lang: 'zh-CN',
      crowded: (carLabel, recCar) => `${carLabel}比较拥挤,请前往${recCar}。`,
      emergency: (carLabel) => `${carLabel}检测到紧急情况,工作人员正在赶来。`,
      lost: (carLabel) => `${carLabel}检测到遗留物品。`,
      arrival: (carLabel, occ) => `${carLabel}的乘客率为百分之${occ}。`,
    },
    'ja': {
      lang: 'ja-JP',
      crowded: (carLabel, recCar) => `${carLabel}は混雑しています。${recCar}にお移りください。`,
      emergency: (carLabel) => `${carLabel}で緊急事態が検知されました。乗務員が確認中です。`,
      lost: (carLabel) => `${carLabel}で忘れ物が検知されました。`,
      arrival: (carLabel, occ) => `${carLabel}の混雑率は${occ}パーセントです。`,
    },
  };

  function speak(text, langCode = 'ko-KR') {
    if (!('speechSynthesis' in window)) return false;
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = langCode;
      u.rate = 1.05;
      u.pitch = 1.0;
      window.speechSynthesis.speak(u);
      return true;
    } catch {
      return false;
    }
  }

  function announce(kind, lang, params) {
    const t = TTS_TEMPLATES[lang] || TTS_TEMPLATES['ko'];
    const fn = t[kind];
    if (!fn) return false;
    const text = fn(...params);
    return speak(text, t.lang);
  }

  // ============== 토스트 ==============
  function pushToast(stackEl, incident) {
    if (!stackEl) return;
    const sev = incident.severity || 'low';
    const el = document.createElement('div');
    el.className = `toast ${sev}`;
    el.innerHTML = `
      <span class="icon">${TYPE_ICON[incident.type] || '•'}</span>
      <div>
        <div class="title">${TYPE_LABEL[incident.type] || incident.type}</div>
        <div>${incident.msg}</div>
      </div>
    `;
    stackEl.appendChild(el);
    // 자동 제거 (high 6초, med 5초, low 4초)
    const dur = sev === 'high' ? 6000 : sev === 'med' ? 5000 : 4000;
    setTimeout(() => {
      el.classList.add('fade');
      setTimeout(() => el.remove(), 400);
    }, dur);
    // 너무 쌓이면 오래된 것 제거
    while (stackEl.children.length > 5) stackEl.removeChild(stackEl.firstChild);
  }

  // ============== 약자 모드 (시민 앱) ==============
  function applyAccessibilityMode(rootEl, on) {
    rootEl.classList.toggle('a11y', on);
    if (on && document.documentElement) {
      document.documentElement.style.setProperty('--a11y-scale', '1.18');
    } else if (document.documentElement) {
      document.documentElement.style.removeProperty('--a11y-scale');
    }
  }

  global.SafetyFeatures = {
    TYPE_LABEL, TYPE_ICON,
    formatRelTime,
    speak, announce,
    pushToast,
    applyAccessibilityMode,
    TTS_TEMPLATES,
  };
})(window);
