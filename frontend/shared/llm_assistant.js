// LLM 어시스턴트 — 데모용 사전 생성 응답
// 실서비스에선 callLLM을 Claude/HyperClova X/EXAONE API 호출로 교체.
// 데모 안정성/비용 0 확보.

(function (global) {
  'use strict';

  // ============== 운영자 콘솔 응답 ==============
  const OPERATOR_CANNED = [
    {
      keywords: ['평소', '다른', '특이', '비정상', '이상한', '왜', 'anomaly'],
      response: `최근 1시간 패턴 분석 (1주차 EDA 기준):

• 5호차/8호차 점유율 평균 **87%** (평소 동일 시간대 78%) — +9%p 비정상
• 환승 비대칭: 잠실→잠실나루 방향이 평소 대비 +22% 강함
• 약자석 점유율은 평균 수준

**추정 원인**: 인근 행사 또는 일시적 수요 spike
**권고**: 6/7호차 분산 안내 즉시 송출, 다음 편성 5분간 모니터링 강화`,
    },
    {
      keywords: ['응급', '위급', '안전', 'emergency', '사고'],
      response: `현재 안전 감지 요약:

🚨 **응급 1건** — 5호차 좌측 좌석, 비정상 자세 14초 지속
⚠ **이상행동 1건** — 7호차 출입문 부근, 비정상 거리 변화

**즉시 조치**:
1. 5호차 승무원 호출 (무전 채널 12)
2. 다음역 도착 시 의료진 대기 요청
3. 시민 앱 동선 우회 알림 자동 송출 (이미 진행 중)`,
    },
    {
      keywords: ['분산', '안내', '권고문', '방송', '멘트'],
      response: `4개 언어 분산 안내문 (즉시 송출 가능):

🇰🇷 안내드립니다. 5호차가 매우 혼잡합니다. 1호차 또는 8호차로 이동해주시기 바랍니다.

🇺🇸 Car 5 is very crowded. Please move to Car 1 or Car 8 for a more comfortable ride.

🇨🇳 5号车厢非常拥挤,请前往1号或8号车厢。

🇯🇵 5号車が混雑しております。1号車または8号車へお移りください。

→ 패널의 🔊 버튼으로 자동 송출`,
    },
    {
      keywords: ['예측', '미래', '5분', '10분', '앞으로', '곧', 'forecast'],
      response: `다음 5분 예측 (EDA 패턴 + 사이클 기반):

• 5호차: 87% → **94%** (임계 임박)
• 8호차: 65% → 72%
• 1호차: 38% → 45% (한산 유지)

**권고**: 지금 분산 안내 송출. 5분 후 임계점 돌파 예상 → 선제 대응이 사후보다 효과 ↑`,
    },
    {
      keywords: ['약자', '휠체어', '임산부', '노약자', '배려'],
      response: `약자석/휠체어 공간 모니터:

• 5호차: 4/4 점유, **인근 입석 차단 1건** (휠체어 진입 곤란)
• 8호차: 2/4 점유, 차단 없음

**권고**: 5호차에 입석 분산 멘트 송출 — "약자석 인근 통로를 비워주세요"
시민 앱 약자 모드 사용자 자동 알림 동시 발송됨`,
    },
    {
      keywords: ['에너지', '운행', '간격', '효율', '절감', 'esg'],
      response: `시간대별 운행 빈도 최적화 제안:

• 14~16시 평균 점유율 28% — **5분 간격 → 8분 간격** 권장
• 예상 절감: 일일 전력 약 **6.4%** (지하철 운행 전력 기준)
• 영향: 평균 대기 +1.4분, 시민 만족도 영향 미미 (한산 시간대)

**ROI**: 연 환산 약 1.2억원 절감 추정 (2호선 본선 기준)`,
    },
  ];
  const OPERATOR_DEFAULT = `BEV 운영자 어시스턴트입니다. 이런 질문 해보세요:
• "지금 가장 위급한 칸은?"
• "오늘 잠실역 평소와 다른 점"
• "다음 5분 어떻게 변할까?"
• "분산 안내 권고문 작성해줘"
• "약자석 차단된 칸 처리 방법"
• "운행 간격 효율화 제안"`;

  // ============== 시민 앱 응답 ==============
  const CITIZEN_CANNED = [
    {
      keywords: ['강남', '강남역'],
      response: `강남역까지 옵션 비교:

🚇 **2호선 직통** — 약 22분 · 다음 1호차 (38%) 추천
🚌 간선 142 → 환승 — 약 28분 · 1순위 차량 (52%)

→ **2호선 1호차**가 가장 한산하고 빠름. 승강장 마커 1번으로 25m 이동.`,
    },
    {
      keywords: ['홍대', '홍대입구'],
      response: `홍대입구역까지:

🚇 **2호선 직통** — 약 31분 · 1호차 (38%) 추천
🚌 환승 옵션은 시간이 더 걸려 비추

→ 마커 1번 이동 후 1호차 탑승. 좌석 가능 확률 ~70%.`,
    },
    {
      keywords: ['한산', '비어', '덜 혼잡', '여유'],
      response: `지금 가장 한산한 차량:

**2호선 1호차** — 38% (편성 평균 -40%p)
위치: 승강장 마커 1번 (35m)
도착: 1분 12초 후
좌석 가능 확률: 약 70%`,
    },
    {
      keywords: ['휠체어', '저상', '약자', '엘리베이터', '유아차'],
      response: `휠체어/유아차 동선:

🛗 가까운 엘리베이터: 7번 출구 (52m)
🚇 저상 차량: 5호차에 **약자석 2석** 비어있음 + 휠체어 공간 진입 가능
👤 도움 요청: 역무원 호출 (앱 우상단)

승강장 마커 5번까지 안내합니다.`,
    },
    {
      keywords: ['빠른', '빨리', '최단', '제일 빨리'],
      response: `현재 시각 기준 가장 빠른 옵션:

**2호선 다음 열차** — 1분 12초 후 도착
1호차가 가장 한산해서 승하차 빠름

→ 승강장 마커 1번으로 30초 안에 이동 권장`,
    },
  ];
  const CITIZEN_DEFAULT = `이렇게 물어보세요:
• "강남역까지 빠르게"
• "지금 가장 한산한 차"
• "휠체어로 갈 수 있어?"
• "홍대까지 가는 법"`;

  function matchCanned(prompt, db, fallback) {
    const lower = prompt.toLowerCase().trim();
    if (!lower) return fallback;
    for (const entry of db) {
      if (entry.keywords.some(k => lower.includes(k.toLowerCase()))) {
        return entry.response;
      }
    }
    return fallback;
  }

  // 라이브 LLM 통합 시 여기를 fetch로 교체
  async function callLLM(prompt, mode = 'operator') {
    // 약간의 지연 — LLM 처리 중인 것처럼 보이게
    await new Promise(r => setTimeout(r, 280 + Math.random() * 220));
    if (mode === 'operator') {
      return matchCanned(prompt, OPERATOR_CANNED, OPERATOR_DEFAULT);
    }
    return matchCanned(prompt, CITIZEN_CANNED, CITIZEN_DEFAULT);
  }

  // 타이프라이터 효과 (생성 중 느낌)
  function streamTo(el, text, opts = {}) {
    const speed = opts.speed ?? 14;        // ms per char
    el.textContent = '';
    let i = 0;
    return new Promise((resolve) => {
      function step() {
        const chunk = Math.max(1, Math.floor(text.length / 80));
        el.textContent = text.slice(0, i + chunk);
        i += chunk;
        if (i >= text.length) {
          el.textContent = text;
          resolve();
        } else {
          setTimeout(step, speed);
        }
      }
      step();
    });
  }

  // ============== 자연어 사고 분류 (LLM 활용 사례 #2) ==============
  // 안전 감지 raw 메시지를 자연어 카테고리/긴급도로 정규화
  // 데모: 사전 룰 기반. 실서비스: LLM zero-shot 분류
  function classifyIncident(rawMsg) {
    const m = rawMsg.toLowerCase();
    if (m.includes('응급') || m.includes('비정상 자세') || m.includes('누움')) {
      return { category: 'medical', urgency: 'critical', recommendedAction: '의료진 호출 + 다음역 정차 시 대기' };
    }
    if (m.includes('이상행동') || m.includes('거리 변화')) {
      return { category: 'behavioral', urgency: 'monitor', recommendedAction: '승무원 시각 확인 권고' };
    }
    if (m.includes('잔존') || m.includes('분실')) {
      return { category: 'lost_item', urgency: 'low', recommendedAction: '하차역 도착 후 회수' };
    }
    if (m.includes('무임')) {
      return { category: 'fare', urgency: 'low', recommendedAction: '데이터 누적, 분기 보고서 반영' };
    }
    return { category: 'unknown', urgency: 'monitor', recommendedAction: '수동 확인' };
  }

  global.LLMAssistant = {
    callLLM,
    streamTo,
    classifyIncident,
    OPERATOR_DEFAULT,
    CITIZEN_DEFAULT,
  };
})(window);
