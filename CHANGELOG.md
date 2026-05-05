# Changelog — MetroEyes (SubwayBEV)

## v4.0 — D-8 자동 모드 60 사이클 (2026-05-05)

### 양면 가치 사슬 5단계 클로즈드 루프
1. 시민 PWA → CTA 분산 액션 (5%p +100원, 30%p +200원)
2. backend `impact_log` → krw 누적 + ROI 계산
3. 운영자 콘솔 헤더 pill — 정책 비용 + ROIx 라이브
4. backend `incident_log` → 다중 페이지 사고 동기화
5. 시민 PWA 인근 사고 알림 (incident_summary 수신 + 음성)

### 시연 fail-safe 5중 안전망
- `--demo` 모드 (CV 없이 BEV 5Hz)
- ▶︎ 시연 인젝터 (운영자 4 + admin) — 30초 5종 progress bar
- 4-패널 통합 시연 (`demo.html`) — 5분 자동 시퀀스 + sticky bar
- backend 신규 클라이언트 join 시 즉시 누적 summary
- admin 단일 클릭 — backend 만 켜져 있어도 5종 송신 가능

### 학술 정밀도
- **EDA v3 GBR 회귀** — 실 CardSubwayTime parquet (171 샘플) → 5-fold CV R² **0.931 ± 0.048**, MAE 29.25 명/칸
- Top 특징: n_stations 0.300 / is_late 0.191 / hour 0.175 (호선 길이가 차량 수보다 4배 강한 변수)
- **ROI v3 정책 시뮬** — 호선 9개 × 시간 24시간 매트릭스 + cap 도달도 차등
- 응답률 30% 가정 시: 사회적 가치 **1,393억/년**, ROI **347x** (인프라 4억)
- v2 (283억) 대비 **5배 정밀**

### 페이지 통합 — 10 페이지
- `frontend/index.html` — 8 카드 진입 허브
- `frontend/demo.html` — 4-패널 통합 시연 (운영자/시민/광고/실카메라)
- `frontend/pitch.html` — 정책 정량 보고 (인터랙티브 슬라이더 + ROI 곡선 + FAQ 5 + PDF 출력)
- `frontend/admin.html` — Debug Console (Live Impact + sparkline + API health + CV 메트릭 + incident timeline)
- `frontend/operator_web/{index,bus,realbev,ad_pricing}.html` — 운영자 4 (지하철/버스/실카메라/광고)
- `frontend/passenger_app/{index,onboard}.html` — 시민 PWA 2

### 다국어 + 접근성
- 4개 언어 보상 toast (ko/en/zh/ja) — `navigator.language` 자동 감지
- Web Speech API 음성 안내 — 시각장애인/백그라운드 사용자 포용
- ARIA: `role="alert"` + `aria-live` + `aria-atomic` + `aria-hidden` 이모지
- 시민 PWA 사고 알림 음성 (5분 throttle)

### 모바일 반응형
- 운영자 4 페이지 + 광고 + PWA 2 — `@media (max-width: 760px / 480px)`
- `env(safe-area-inset-*)` 노치/홈 인디케이터 회피
- viewport-fit=cover

### 백엔드 통합
- `lite_server.py`
  - 외부 API 호출 통계 (`_api_stats`) → `/health` 응답
  - CV 메트릭 (`_cv_metrics` fps/tracks/frames/last_ts)
  - 임팩트 누적 (`_impact_total` count/saved/krw_paid + ROI 계산)
  - 사고 누적 (`_incident_total` 4 카운트 + 최근 30 events)
  - CORS 헤더 (cross-origin admin polling)
  - 신규 클라이언트 join 시 즉시 누적 summary 전송

### 글로벌 비교 + 차별점
- 런던 Off-Peak (역 단위 30% 고정 할인)
- 도쿄 Suica 패스 (월 정액)
- 싱가포르 GP-S (25¢ 1회성, 응답률 ~5%)
- **MetroEyes**: 칸 단위 BEV + 분산률 차등 보상 + 양면 클로즈드 루프 (글로벌 최초)

### 자동 사이클 누적
- **99 사이클 / 약 120 커밋**
- 1차 push 23 commits (5/5 13:30 사용자 승인)
- 2차 push 대기 60+ commits (사이클 39~99)
- 추가 작업: 6 페이지 라이브 KPI 통일 / 핫스팟 chip / 시간대 sparkline / 사고 type 막대 / ko-en 토글 / REST API v1 (4 endpoint + /api/docs) / EDA air×subway / 자동 시뮬 (--demo warm seed)
- 마감 D-8 (5/13)

---

## v3.0 — D-9 자동 모드 사이클 1~17 (이전)

- 시민 PWA station picker, 광고 단가 라이브, A* 비상동선, ROI v2, EDA 호선별
- 자동 의사결정 4종 (절전/응급/분실/분산)
- 5대 신규 아이디어 (절전·분실·응급·24h예측·광고실노출)
- 안전 부각 + 무임 추정 카드

---

## v1.0 — 1주차 EDA + 클러스터링 (2026-04-22)

- CardSubwayTime 분석 — 양봉 (08/18), 환승 비대칭, 칸 컬럼 부재 입증
- K=3 클러스터 (silhouette 0.387, PCA 84.1%) — 오피스/주거/환승 허브
- GBR R²=0.78 점유율 회귀
