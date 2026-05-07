# MetroEyes

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-7dd3d3.svg)](LICENSE)
[![ROI](https://img.shields.io/badge/ROI%20v3-347x-10b981.svg)](frontend/pitch.html)
[![Social Value](https://img.shields.io/badge/사회적_가치-1%2C393억%2F년-7dd3d3.svg)](frontend/pitch.html)
[![EDA](https://img.shields.io/badge/EDA%20v3%20R²-0.931-f59e0b.svg)](scripts/eda_carload_v3_real.py)
[![Cycles](https://img.shields.io/badge/자동_사이클-388회-a78bfa.svg)](CHANGELOG.md)
[![REST API](https://img.shields.io/badge/REST_API-v1-38bdf8.svg)](http://localhost:8765/api/docs)
[![CI](https://github.com/leelang7/MetroEyes/actions/workflows/ci.yml/badge.svg)](https://github.com/leelang7/MetroEyes/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/regression_tests-197회귀_가드-10b981.svg)](tests/)
[![Lang](https://img.shields.io/badge/lang-ko%20·%20en%20·%20zh%20·%20ja-ef4444.svg)](frontend/passenger_app/index.html)

> *"테슬라가 도로를 BEV로 보듯, MetroEyes는 도시 교통 전체를 본다."*

🇺🇸 [English README](README.en.md)

**라이브 데모 (외부 고정 URL)**: https://leelang7.github.io/MetroEyes/
> 너 PC backend(ngrok 영구 도메인)에 자동 wss 연결. PC 켜둔 상태에서 누구든 접속하면 LIVE.

---

## 💡 평가위원 / Reviewers — 5 분 안에 핵심 파악

> 처음 보시는 분은 아래 5 자료부터 — 모두 1차/2차 심사 정량 가중치와 1:1 매핑됨.

| 우선순위 | 자료 | 1줄 설명 | 시간 |
|---:|---|---|---:|
| **1** | [📊 frontend/onepager.html](frontend/onepager.html) | A4 1-Pager — 핵심 KPI / 6 차별성 / 4 도시 비교 / 사업화 BM **(4언어)** | 1분 |
| **2** | [🎬 frontend/demo.html](frontend/demo.html) | 5 분 통합 자동 시연 — 4 패널 동시 + 14 stage SCRIPT | 5분 |
| **3** | [📈 frontend/pitch.html](frontend/pitch.html) | 정량 보고 — Monte Carlo CI + 호선별 ROI + 호선×시간 매트릭스 | 5분 |
| **4** | [🎯 docs/SUBMISSION_INDEX.md](docs/SUBMISSION_INDEX.md) | 평가 지표 ↔ 산출물 ↔ CI 가드 자기 채점 (1차 105 + 2차 100) | 3분 |
| **5** | [💬 docs/QA_PREPARATION.md](docs/QA_PREPARATION.md) | 18 예상 질문 + 30초 self-pitch (5 카테고리) | 5분 |

**짧은 요약**: 자체 CV BEV + 9 공공 API + 시민 인센티브 3 축 통합 시스템.
정책 ROI v3 + Monte Carlo 1,000 회 95% CI 로 사회 가치 **1,393억/년 [CI 1,064~1,808억]** 정량 도출.
2호선 ROI 708x — 정책 결정 즉답. 8단 fail-safe + 177 회귀 가드 + 4 언어 i18n production-grade.

**문서 추가 (장애·운영)**: [📕 docs/RUNBOOK.md](docs/RUNBOOK.md) — 9 시나리오 1줄 복구 · [📖 docs/PROPOSAL.md](docs/PROPOSAL.md) — 상세 기획서 v3


**핵심 KPI (정책 ROI v3, 응답률 30% 가정)**:
- 순 사회적 가치 **1,393억/년** · ROI **347x** · 인프라 4억 (134역 우선)
- 절감 시간 473.4M분/년 · cap 평탄화 −0.66%p · 2호선 단독 157M분 절감
- **차등 인센티브 4단** (₩100/₩200/₩300/₩400) — backend 자동 가산, EDA 정량 매핑

**3 EDA 실 데이터 검증**:
- **분산 효과**: σ −9.0% / 피크 평균 −13.5% / 비피크 +5.6% / 비율 1.78→1.46
- **OD 비대칭**: 삼성(무역센터) OFF/ON 12.4x (출근 도착) / 시청 ON/OFF 4.9x (퇴근 출발)
- **환승역 비대칭**: 충무로 4호선 +0.56 vs 3호선 −1.00 (diff +1.56) / 연신내 +1.44

**진입**: [`frontend/index.html`](frontend/index.html) — 8장 카드 허브 (📊 정책 보고 / 🎬 통합 시연 / 🚇 운영자 / 📱 시민 / 🛠 디버그)

**자동 382 사이클 누적 결과** (D-5, 2026-05-13 마감):
- ✅ 양면 가치 사슬 5단계 (시민 분산 → backend krw → 운영자 ROI → backend incident → 시민 알림)
- ✅ 시연 fail-safe **8중**: `--demo` + 30s 인젝터 + 5분 sticky bar + backend join summary + admin 단일 클릭 + fake impact seed + Docker compose + GitHub Actions CI
- ✅ 다국어 4개 (ko/en/zh/ja) **11 페이지 패리티** (운영자 4 + 시민 2 + 메타 5) + Web Speech + ARIA
- ✅ 모바일 반응형 (운영자 4 + 광고 + 시민 PWA) + safe-area-inset
- ✅ EDA v3 실 parquet GBR R²=0.931 + **분산 효과 EDA** (σ −9% / 피크 −13.5% / 비피크 +5.6% 실 데이터 검증)
- ✅ 11 페이지 통합 + ROI 인터랙티브 슬라이더 + **±15% 민감도 CI band**
- ✅ pitch.html PDF 인쇄 친화 + FAQ 8개 (IDEA-9 접근성 제도 포함) + 글로벌 비교 + 분산 효과 4-KPI
- ✅ **비상 동선 K-means(K=4) + 헝가리안 1:1 출구 매칭** (단일 출구 baseline 대비 cost 절감 정량화)
- ✅ **OpenAPI 3.0 spec** (`/api/openapi.yaml`) — Swagger/Redoc/Postman 자동 임포트
- ✅ **IDEA-7 임산부석** + **IDEA-8 병목 사전 경고** (cycle 226 — 칸 단위 BEV ROI 응용)
- ✅ **IDEA-9 도착 알림 5중 모달리티** (cycle 286-310, PWA v4.10) — 시각/햅틱/beep/4언어 음성/시스템 알림 + Wake Lock + SW notificationclick + 최근 도착지 MRU 5개 + persistence (2시간 만료) + ETA 분 표시 + 사전 테스트 버튼 + 안전망 인디케이터 (🔆🔔⚙) + 사용 히스토리 카운터 (노이즈 캔슬링/이어폰/청각 약자 42만 명 + 노캔 1,200만 잠재 사용자, 접근성 제도 직결)
- ✅ **CI 15 jobs + pytest 회귀 가드 177건** (cycle 318-382): OpenAPI(4) + ROI v3(5) + dispersion(6) + OD/transfer(6) + bonus(6) + figs(3) + pitch(6) + impact(5) + cycle 356-382 신규 78건 (LLM/환경/A*/PWA/demo/i18n/ROI panel/heatmap/narration/onepager/proposal v3/SLIDES v3/Monte Carlo CI/RUNBOOK/QA/SUBMISSION_INDEX/reviewer guide/changelog/submission ship-gate) — 광고 KPI ↔ 코드 ↔ 그림 ↔ 발표 자료 ↔ canonical JSON 모두 자동 정합 검증
- ✅ **canonical KPI drift 자동 차단** (cycle 375): 광고 1,393억 / 347x / 2호선 157M / CI [1,064~1,808] 모든 자료 동시 일치 강제 — D-day 제출 직전 cycle 374 같은 KPI 충돌 사고 자동 감지
- ✅ **submission ship-gate** (cycle 380): `python scripts/submission_check.py --ci` 1초 내 12 항목 PASS/WARN/FAIL — 매 push 마다 자동 제출 가능 검증

---


**4중 데이터 융합** + **자체 CV** + **시민/운영자 듀얼 도메인** — 지하철·버스 둘 다, 시민의 한 번의 탑승 결정을 더 정확하게.

> 코드/디렉토리는 `subwaybev_*` 식별자를 보존 — 빌드 호환 유지. UI 표시만 MetroEyes.

## 라이브 데모 (3분)

**가장 빠른 시연 (CV 모델 없이)**:
```powershell
python -m src.cv.lite_server --port 8765 --demo
```
→ fake BEV 트랙 5Hz broadcast + 모든 외부 API 라이브 호출 활성. 운영자 콘솔 → ▶︎ 시연 모드 30초 자동 재생.

**한 줄 도커 (backend + frontend 통합)**:
```bash
docker compose up -d
```
→ backend `:8765` + frontend `:5173` 즉시 기동. `.env` 자동 로드. 어떤 환경에서도 동일 검증.

**발표 영상 5분 캡처 가이드**: [`docs/RECORDING_GUIDE.md`](docs/RECORDING_GUIDE.md) — 10단 시퀀스 + OBS 설정 + 한국어 멘트.

**발표 자료 6종**:
- [`docs/SLIDES.html`](docs/SLIDES.html) — 한쇼 16:9 슬라이드 (PDF 출력 가능)
- [`docs/SLIDES_DECK.md`](docs/SLIDES_DECK.md) — 슬라이드 텍스트 (한쇼 복붙용)
- [`docs/PROPOSAL.md`](docs/PROPOSAL.md) — 1차 제안서 본문
- [`docs/INNOVATION_TRIZ.md`](docs/INNOVATION_TRIZ.md) — TRIZ 6 모순 분석
- [`docs/ARCHITECTURE_VIEW.html`](docs/ARCHITECTURE_VIEW.html) — 시스템 4 계층 다이어그램
- [`docs/SUBMISSION_GUIDE.md`](docs/SUBMISSION_GUIDE.md) — 1차 접수 체크리스트

**완전한 실데이터 흐름**:
1. 백엔드: `.venv\Scripts\python.exe -m src.cv.tesla_bev --port 8765 --model yolo11s.pt --imgsz 1280 --conf 0.18`
2. 영상 피더: `.venv\Scripts\python.exe scripts\feed_video.py`
3. (옵션) ngrok 외부 노출: `ngrok http 8765`
4. 화면들 모두 같은 백엔드의 라이브 신호를 공유:
   - 시민 PWA: `frontend/passenger_app/index.html` — GPS → 가까운 역, 라이브 칸별 점유율, 역세권 인구 chip
   - 시민 PWA 탑승 후: `frontend/passenger_app/onboard.html` — 차내 점유율 라이브
   - 운영자 콘솔: `frontend/operator_web/index.html` / `bus.html` — 4중 fusion-strip
   - 운영자 3D BEV: `frontend/operator_web/realbev.html` — Three.js 3D + fusion-strip + 역 picker
   - Flutter 폰 앱: `mobile_app/` — ngrok wss로 외부 망 동작

또는 한 줄로:

```powershell
pwsh scripts\start_demo.ps1
```

## 데이터 출처

| 데이터셋 | API | 사용처 |
|---|---|---|
| 서울 실시간 도시데이터 — 통합 (인구·버스·도로·주차·따릉이·날씨·공기·UV·24h예보·상권) | `citydata` | 4중+ 라이브 융합 |
| 서울 실시간 도시데이터 — 인구·혼잡도 | `citydata_ppltn` | 역세권 컨텍스트 |
| 자치구 일별 생활인구 | `SPOP_DAILYSUM_JACHI` | 일별 트렌드 |
| 시간대별 승하차 (CardSubway) | `CardSubwayStatsNew` | ML 학습 입력 |
| 도시철도 실시간 도착 (TOPIS) | `realtimeStationArrival` | 도착 ETA — 별도 키 |
| 문화 행사 예약 | `ListPublicReservationCulture` | 인구 영향 신호 |
| 따릉이 정류장 실시간 | `bikeList` / `tbCycleStationInfo` | 환승 옵션 |

키는 [data.seoul.go.kr](https://data.seoul.go.kr) 마이페이지에서 발급. `.env`에:
- `SEOUL_OPENDATA_API_KEY` — 일반 데이터 (citydata, CardSubway, 행사 등)
- `SEOUL_SUBWAY_ARRIVAL_KEY` — 도시철도 실시간 도착 (별도 신청)
- `SEOUL_BUS_ARRIVAL_KEY` — 버스 도착 (있으면)

## 백엔드 WS 컨트롤 메시지

운영자 콘솔 / 시민 PWA / Flutter 폰이 모두 이 컨트롤을 사용:

| `type` | 인자 | 응답 |
|---|---|---|
| (JPEG bytes) | — | `{tracks, fps, frame_idx}` BEV 페이로드 broadcast |
| `arrival_query` | stationName, line | `{type:'arrival', items, simulated}` |
| `population_query` | poi | `{type:'population', congest_lvl, ppltn_min/max, ...}` |
| `citydata_query` | poi | `{type:'citydata', 통합 (날씨·도로·환승·24h예보·...)}` |
| `events_query` | poi | `{type:'events', events:[{name, place, v_max, dist_km}]}` 행사 list |
| `predict_occupancy` | hour, line, stationName | `{type:'occupancy_predict', predicted}` ML 곡선 한 점 |
| `model_metrics_query` | — | `{type:'model_metrics', mae_val, r2_val, mae_cv5, ...}` |
| `impact_log` | station, car, saved_pct, krw | broadcast `{type:'impact_summary', total_count, avg_saved_pct, saved_min_total, value_won, krw_paid, roi_x, est_response_rate, top_station}` |
| `predict_surge` | poi, hours_ahead | `{type:'surge_forecast', peaks, hourly}` 24h 폭증 예측 |

## 실행 (sandbox 환경 우회)

PowerShell sandbox에서 child Python이 stdout buffer로 stuck 되는 환경에서는 새 콘솔 창으로 띄우는 것이 가장 안전:

```powershell
pwsh scripts\start_demo.ps1            # backend + publisher + ngrok 새 콘솔 3개
pwsh scripts\start_demo.ps1 -NoNgrok   # 외부 노출 없이 (USB/로컬만)
pwsh scripts\start_demo.ps1 -Stop      # 모두 종료
```

또는 직접 두 콘솔에서:

```powershell
# 콘솔 1
cd C:\Users\leesc\Documents\Seoul
.\.venv\Scripts\python.exe -u -m src.cv.tesla_bev --port 8765 --model yolo11s.pt --imgsz 1280 --conf 0.18

# 콘솔 2 (영상 피더)
cd C:\Users\leesc\Documents\Seoul
.\.venv\Scripts\python.exe scripts\feed_video.py
```

---

## 디렉토리 구조

```
.
├── data/                  # 서울 열린데이터 + 시뮬 데이터
│   ├── raw/               # 원본 (git 제외)
│   ├── processed/         # 전처리 산출물
│   └── sim/               # 시뮬레이터 출력
├── notebooks/             # EDA, 시각화, 실험 기록
├── src/
│   ├── cv/                # 실시간 카메라 → YOLO + BoT-SORT → BEV
│   ├── data_pipeline/     # 데이터 수집/전처리 (서울 OpenAPI 클라이언트)
│   ├── models/            # BEV 아키텍처 (multi-view → BEV → occupancy/count)
│   ├── training/          # 학습 루프
│   ├── inference/         # 엣지 추론(Jetson) + 후처리
│   ├── api/               # FastAPI 백엔드 (WebSocket 스트리밍)
│   └── utils/
├── frontend/
│   ├── operator_web/      # 운영자 대시보드 (라이브 BEV + 4중 fusion)
│   ├── passenger_app/     # 시민 PWA
│   └── shared/            # BEV 엔진 / 안전 기능 / LLM 어시스턴트
├── mobile_app/            # Flutter 네이티브 폰 앱
├── configs/               # 실험/배포 설정 (yaml)
├── scripts/               # CLI 스크립트 (학습/캡처/데모 시작)
└── tests/
```

---

## 빠른 시작

### 1. Python 환경

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

또는 conda:

```bash
conda env create -f environment.yml
conda activate subwaybev
```

### 2. CUDA / PyTorch 확인

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

### 3. 실 카메라 BEV 라이브 파이프라인

```bash
# (옵션) 호모그래피 캘리브레이션 — 4점 시계방향 클릭: 좌상→우상→우하→좌하
python -m src.cv.calibrate --cam ceiling --source 0

# 백엔드 (YOLO + BoT-SORT + WebSocket 8765)
python -m src.cv.tesla_bev --port 8765 --model yolo11s.pt --imgsz 1280 --conf 0.18

# 정적 파일 서버
cd frontend && python -m http.server 5173

# 브라우저
#  http://localhost:5173/operator_web/realbev.html   ← 운영자 3D
#  http://localhost:5173/passenger_app/index.html    ← 시민 PWA
```

비디오 파일 입력은 publisher로:
```bash
python scripts/feed_video.py path/to/clip.mp4
```

---

## ML 모델 학습 (선택)

`CardSubwayStatsNew` + 역 클러스터링 → GradientBoosting 점유율 회귀:

```bash
python scripts/cluster_stations.py            # 역 클러스터 산출 (먼저 1회)
python scripts/train_occupancy.py --month 202602
```

→ `outputs/models/occupancy_lgbm.joblib` + 검증 metrics + 산점도/특징 중요도 그림.
백엔드는 모델 파일이 있으면 lazy load해 `predict_occupancy` WS 컨트롤로 응답.

---

## 정책 ROI v3 (호선 × 시간대 차등 모델)

```bash
python scripts/policy_roi_v3.py
```

산출:
- `outputs/policy_roi_v3_report.json` — 5단계 시나리오 + 호선별 절감 매트릭스
- `outputs/policy_roi_v3_matrix.png` — 호선 9 × 시간 24 절감 분 히트맵

**v2 대비 진화**: 호선별 cap 도달도 (1호선 0.55 vs 9호선 1.10) 차등 + 출퇴근 응답률 비대칭 (8시 0.7 / 18시 1.0) + cap 평탄화 효과. 응답률 30% 시 v2 283억 → v3 **1,393억/년 (5x 정밀화)**.

자세한 분석: [`frontend/pitch.html`](frontend/pitch.html) (한 페이지 정량 보고)

---

## 오픈 REST API v1 + OpenAPI 3.0

backend `lite_server.py` 가 10 endpoint 제공 (REST API v1 9 + 자동 docs UI 1) — 모두 CORS 허용:

| Endpoint | 응답 | 용도 |
|---|---|---|
| `GET /health` | 시스템 상태 (api/cv/incidents/msg) | health check |
| `GET /api/v1/roi_curve` | 0~80% 81 샘플 ROI | 정책 시뮬 외부 도구 |
| `GET /api/v1/impact` | 누적 분산 임팩트 + tier_counts | 라이브 KPI |
| `GET /api/v1/incidents` | 사고 6 카운트 (IDEA-7/8 priority_seat/bottleneck 포함) + 30 events | 라이브 모니터링 |
| `GET /api/v1/dispersion` | σ/peak/offpeak 정적 검증 + 라이브 응답률 추정 | 분산 효과 시각화 |
| `GET /api/v1/od_asymmetry` | 현 시각(AM/PM) 자동 매칭 + 우선 분산 추천 역 TOP 5 | 운영자 정책 우선순위 |
| `GET /api/v1/transfer_priority` | 환승역 호선 간 비대칭 차이 TOP 5 (현 시각 AM/PM) | 환승 흐름 분산 정책 |
| `GET /api/v1/policy_summary` | 정책 정의 + 라이브 impact + dispersion + **incident_breakdown 6 type** + EDA 통합 | Excel/Power BI 단일 폴링 |
| `GET /api/openapi.yaml` | OpenAPI 3.0 spec | Swagger/Redoc/Postman 자동 임포트 |
| `GET /api/docs` | 자동 HTML 명세 페이지 | curl/Postman 대체 |

```bash
# 예시: ROI 곡선 fetch
curl http://localhost:8765/api/v1/roi_curve | jq '.curve | map(select(.rate == 0.30))'

# 예시: 분산 효과 정적 검증 + 라이브 추정
curl -s http://localhost:8765/api/v1/dispersion | jq '{static: .static, live: .live}'

# 예시: 현 시각 OD 우선순위 (AM 7~11 → 출근 도착 / PM 17~21 → 퇴근 출발)
curl -s http://localhost:8765/api/v1/od_asymmetry | jq '{type: .priority_type, stations: .priority_stations | map(.station)}'

# 예시: OpenAPI 3.0 spec 다운로드
curl -o openapi.yaml http://localhost:8765/api/openapi.yaml
```

---

## License

내부 개발 — 외부 공개 미정.
