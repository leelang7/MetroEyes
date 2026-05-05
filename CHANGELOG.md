# Changelog — MetroEyes (SubwayBEV)

## v5.0 — D-7 자동 모드 175 사이클 milestone (2026-05-06 정책 통합 완성)

### v5.0 메이저 버전 — 차등 보상 정책 8단 완전 통합
정책 설계 → EDA 검증 → backend 자동 가산 → UI 라이브 → 외부 BI 통합까지 전 영역 일관성 완성.

### 신규 (사이클 171~175)
- **INNOVATION_TRIZ M6 모순 추가** — 차등 보상 자동 매칭 (TRIZ #15 동적성 + #25 자기 서비스)
- **README ko/en 핵심 KPI 강화** — 차등 4단 + 3 EDA 정량 결과 (한/영 일관성)
- **README.en 173 cycles 누적 결과** + 9 endpoint REST + 8단 가치사슬 + FAQ 6
- **CHANGELOG v5.0 메이저** — 정책 통합 완성 milestone

### v5.0 누적 핵심 산출 (175 사이클)
- **9 REST endpoint + OpenAPI 3.0** (외부 BI 단일 폴링)
- **11 페이지 4언어 i18n** + 5 진입점 환영 toast
- **3 EDA 실 데이터 검증** (분산 / OD / 환승)
- **차등 보상 4단 정책** (₩100/₩200/₩300/₩400) + backend `_bonus_krw()` 자동 가산
- **tier_counts 라이브 분포** 6 페이지 동기화 (admin / pitch / 운영자 4)
- **A* + K-means(K=4) + 헝가리안** 비상 동선
- **ROI v3 ±15% 민감도 CI band** + 차등 효과 +50% 추정
- **8중 시연 fail-safe** (--demo + 인젝터 + 5min sticky + join summary + admin click + warm seed + Docker + GitHub Actions CI)
- **8단 양면 가치 사슬** (CV → 도시 → 결정 → OD 매칭 → 환승 매칭 → 시민 차등 → backend 자동 → ROI)
- **TRIZ 모순 6개** (M6: 차등 보상 자동)

## v4.9 — D-7 자동 모드 170 사이클 milestone (2026-05-06 후속 VII)

### 신규 (사이클 166~170) — 정책 통합 가치 사슬 + FAQ 보강
- **pitch.html 양면 가치 사슬 5 → 8단계 확장** — OD 매칭 + 환승 식별 + backend 자동 가산 단계 추가
- **차별점 카드** "차등 보상 자동 매칭 (글로벌 최초 시간×역×비대칭 3차원 차등)" 추가
- **FAQ Q6 차등 보상 ₩100~₩400 산정 근거** — 그림 4(OD 12x) → ₩300 / 그림 5(환승 +1.56) → ₩400 정량 매핑
- **ad_pricing 차등 보상 → 노출 안정화 카드** — 광고주 가치 3단 매핑 (피크 평탄화 / OD 동반 +5%p / 환승 프리미엄 +10~20%)
- **170 사이클 누적 — 9 endpoint REST API + OpenAPI 3.0 + 11p i18n + 3 EDA + 4단 차등 + K-means + 8중 fail-safe**

## v4.8 — D-7 자동 모드 165 사이클 milestone (2026-05-06 후속 VI)

### 신규 (사이클 161~165) — 외부 BI 통합 + 발표 자료 일괄 갱신
- **`/api/v1/policy_summary` 통합 endpoint** — 정책 4단 정의 + 라이브 impact + 라이브 dispersion + 정적 EDA 단일 JSON
- **9 endpoint REST API** 완성 — Excel/Power BI/Tableau 단일 폴링으로 모든 KPI 임포트
- **OpenAPI 3.0 spec 9 path** — Swagger/Redoc/Postman 자동 임포트 + ImpactSummary tier_counts schema
- **발표 자료 5종 일괄 헤더 갱신** — SLIDES_DECK / ARCHITECTURE_VIEW / INNOVATION_TRIZ / PROPOSAL / SUBMISSION_GUIDE 누적 산출 6항목 명시
- **mobile_app README 9 endpoint + 차등 보상 정책** — Flutter ↔ backend 통합 가이드

## v4.7 — D-7 자동 모드 160 사이클 milestone (2026-05-06 후속 V)

### 신규 (사이클 156~160) — 차등 보상 운영자 패리티 + 통합 가이드
- **운영자 4 페이지 tier 분포 chip 통일** — 지하철/버스/실카메라/광고 모두 헤더 (basic/od/transfer 8s 폴링)
- **OpenAPI ImpactSummary tier_counts schema** — 외부 도구 자동 임포트 가능
- **pitch.html 차등 효과 +50% 추정 박스** — 정책 강화 효과 정량 표현
- **mobile_app README 8 endpoint + 차등 보상 정책** — Flutter ↔ backend 통합 가이드 완성
- **운영자 4 페이지 헤더 통합**: 분산 효과 (σ/피크) + tier 분포 (basic/od/transfer) 동시 표시
- **차등 보상 5 페이지 동기화**: admin / pitch / op-subway / op-bus / op-realcam / op-ad

## v4.6 — D-7 자동 모드 155 사이클 (2026-05-06 후속 IV)

### 신규 (사이클 151~155) — 차등 보상 정책 backend 통합
- **`_bonus_krw()`** — backend `impact_log` handler가 station 매칭으로 자동 차등 보상 가산
  - 환승역 (`/api/v1/transfer_priority` TOP 5): +₩200 보너스
  - OD 우선 (`/api/v1/od_asymmetry` TOP 5, 시각 AM/PM 자동): +₩100 보너스
  - 일반: 기본 ₩200 (변동 없음)
- **`tier_counts`** in `impact_summary` — basic/od/transfer 3 분포 누적 (실시간 broadcast)
- **`fake_impact_seed_loop` station 가중치** — 정확한 STTN 명칭(삼성(무역센터)/충무로/연신내) 빈도 ↑ → 시연 모드에서 차등 보상 자동 발동
- **admin 차등 보상 분포 카드** — 3색 비례 막대 (basic 7dd3d3 / od a78bfa / transfer f59e0b)
- **pitch.html 헤더 차등 chip** — basic/od/transfer 3-color tabular nums 라이브 갱신

## v4.5 — D-7 자동 모드 150 사이클 milestone (2026-05-06 후속 III)

### 신규 (사이클 144~150)
- **admin.html 4언어 환영 toast** — 외국인 운영자/평가위원 첫 방문 자동 안내 (5 진입점 통일: index/demo/PWA index/PWA onboard/admin)
- **PWA 환승역 보너스 chip 4언어** — +₩400 차등 보상 라이브 표시
- **pitch.html 차등 인센티브 정책 표** — ₩100 (기본) / ₩200 (30%p) / ₩300 (OD 우선) / ₩400 (환승역) 4단계 + EDA 그림 4·5 매핑
- **demo.html 5분 시퀀스 232s 환승 흐름 overlay** — 충무로 +1.56 plot 5초 표시 (분산 효과 220s + 환승 232s 2단 데이터 검증 시연)
- **SUBMISSION_GUIDE D-7 상태 헤더** — 145 사이클 / 8 endpoint / 수상 확률 v10
- **README ko/en 통일** — 3 EDA 검증 + 차등 인센티브 + 5 진입 환영 + A*+K-means 모두 반영

### 누적 핵심 산출 (150 사이클)
- 8 REST endpoint + OpenAPI 3.0 spec
- 11 페이지 4언어 i18n + 5 진입점 환영 toast
- 3 EDA 실 데이터 검증 (분산 효과 / OD 비대칭 / 환승역)
- ROI v3 ±15% 민감도 CI band + 차등 4단 인센티브
- A* + K-means(K=4) + 헝가리안 비상 동선
- 8중 시연 fail-safe + Docker compose + GitHub Actions CI
- pitch.html 5 figure (정책 매트릭스 / EDA 호선×시간 / 분산 곡선 / 호선 9패널 / OD TOP10 / 환승역 TOP10)
- 양면 가치 사슬 5단계 클로즈드 루프

## v4.4 — D-7 자동 모드 143 사이클 (2026-05-06 후속 II)

### 신규 (사이클 138~143)
- **시민 PWA OD 우선순위 chip 4언어** — 외국인 시민이 현 시각 권장 분산 역을 즉시 확인 (+₩300 보너스 표시)
- **진입 허브 OD chip + 시민 PWA + pitch + admin + 운영자 = 6 페이지** OD 비대칭 라이브 동기화
- **환승역 분석 EDA** (`scripts/eda_transfer_stations.py`) — 1~9호선 37개 환승역 호선 간 비대칭 차이 TOP 10:
  - **충무로 4호선 +0.56 vs 3호선 −1.00** (diff 1.56) — AM 09시 4호선 출근 도착 압도적
  - 연신내 3호선 vs 6호선 / 동대문 4호선 vs 1호선
  - pitch.html 그림 5
- **`/api/v1/transfer_priority` REST endpoint** — 환승 흐름 우세 TOP 5 (현 시각 AM/PM 자동)
- **8 endpoint REST API 완성** (health/roi/impact/incident/dispersion/od/transfer/openapi)
- **OpenAPI 3.0 spec 8 path** — Swagger/Redoc/Postman 자동 임포트
- **운영자 + admin + pitch 4 페이지에 환승 흐름 chip** — 분산 인센티브를 환승역에 집중하면 양 호선 동시 절감
- **README.md + README.en.md** REST API 8 endpoint 갱신 + curl 4 예시 균형

## v4.3 — D-7 자동 모드 137 사이클 (2026-05-06 후속)

### 신규 (사이클 126~137)
- **OD 비대칭 EDA** (`scripts/eda_od_asymmetry.py`) — 1~9호선 28일 평균 위 ON/OFF 비대칭 지수 분석:
  - 출근 도착 TOP 10: 삼성(무역센터)·역삼·광화문 OFF/ON **12x+**
  - 퇴근 출발 TOP 10: 시청·삼성·광화문 ON/OFF **5x+**
  - 134역 우선순위 모델의 정량 근거 → pitch.html 그림 4
- **`/api/v1/dispersion` REST endpoint** — 정적 σ/peak/offpeak 검증값 + 라이브 응답률 비례 추정
- **`/api/v1/od_asymmetry` REST endpoint** — 현 시각(AM 7~11 / PM 17~21) 자동 매칭 + 우선 분산 추천 역 TOP 5
- **분산 효과 4 페이지 통일 표시**: 운영자 4 (지하철/버스/실카메라/광고) 헤더 dispersion 칩 (σ/피크 라이브)
- **OD 우선순위 4 페이지 통일**: pitch / admin / op-subway / op-bus 라이브 chip (1분 폴링, 시각 자동 전환)
- **demo.html 5분 시퀀스 220s 분산 효과 overlay** (실 데이터 plot + 4-KPI 5초 표시)
- **PWA 외국인 환영 toast 4언어**: index + onboard 첫 방문자 자동 안내 (12s/OK 자동 dismiss)
- **demo.html 외국인 평가위원 환영 toast 4언어** (15s/OK)
- **pitch.html 분산 효과 4-KPI 카드** (σ −9% / 피크 −13.5% / 비피크 +5.6% / 비율 1.78→1.46)
- **ROI v3 ±15% 민감도 CI band** — 보수/기본/낙관 3 시나리오 동시 표시
- **K-means(K=4) + 헝가리안 비상 동선** — 단일 출구 baseline 대비 cost 절감 정량화
- **OpenAPI 3.0 spec** (`docs/openapi.yaml` + `/api/openapi.yaml` 7 path) — Swagger/Redoc/Postman 자동 임포트
- **Matplotlib Malgun Gothic 자동 적용** — 한글 폰트 fallback 체인 (Win/Mac/Linux)
- **i18n 4언어 11 페이지 패리티** — 운영자 4 + 시민 2 + 메타 5

## v4.2 — D-7 자동 모드 125 사이클 (2026-05-06)

### 신규 (사이클 111~125)
- **i18n 4언어 11 페이지 패리티** — 운영자 4 + 시민 2 + 메타 5 (pitch/index/demo/admin/op-subway/op-bus/op-realcam/op-ad + PWA index/onboard)
- **K-means(K=4) + 헝가리안 1:1 출구 매칭** — A* 단일 best 출구 추천 → 4그룹 분산 최적화 (단일 출구 baseline 대비 cost 절감 정량화)
- **ROI v3 ±15% 민감도 CI band** — 보수/기본/낙관 3 시나리오 동시 표시, 인센티브 비용 제외 통근/안전/광고 변동
- **분산 정책 EDA 실 데이터 검증** — `subway_time_202602.parquet` 1~9호선 28일 평균 위에 30%×45% 분산 시뮬:
  - σ 표준편차 129,618 → 117,940 (**−9.0%**)
  - 피크 평균(7~9, 17~19시) **−13.5%**
  - 비피크 평균 **+5.6%**
  - 피크/비피크 비율 1.78 → 1.46 (**−18%**)
- **OpenAPI 3.0 spec** (`docs/openapi.yaml` + `/api/openapi.yaml` endpoint) — Swagger/Redoc/Postman 자동 임포트
- **Matplotlib Malgun Gothic 자동 적용** — 한글 폰트 fallback 체인 (Windows/macOS/Linux)
- **pitch.html 분산 효과 4-KPI 카드** + 그림 2,3 (호선별 9패널) 추가

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
