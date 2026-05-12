# MetroEyes

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-7dd3d3.svg)](LICENSE)
[![CI](https://github.com/leelang7/MetroEyes/actions/workflows/ci.yml/badge.svg)](https://github.com/leelang7/MetroEyes/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-844_passed-10b981.svg)](tests/)
[![Cycles](https://img.shields.io/badge/Auto_Cycles-543-a78bfa.svg)](CHANGELOG.md)
[![Lang](https://img.shields.io/badge/lang-ko%20·%20en%20·%20zh%20·%20ja-ef4444.svg)](frontend/passenger_app/index.html)

> 도시 교통 실시간 BEV 점유 인사이트 시스템 — 지하철·버스 칸별 점유를 분 단위로 보고 시민 분산을 유도한다.

🇺🇸 [English README](README.en.md)

**라이브 데모**: https://leelang7.github.io/MetroEyes/

---

## 💡 평가위원 안내 — 5분 핵심 자료

> 처음 보시는 분: 아래 5개 자료를 순서대로 확인하시면 1·2차 심사 배점 항목을 모두 커버할 수 있습니다.

| 순서 | 자료 | 내용 | 소요 |
|------|------|------|------|
| **1** | [📊 frontend/onepager.html](frontend/onepager.html) | A4 1-Pager — 핵심 KPI · 차별점 6가지 · 4개 도시 비교 **(4언어)** | 1분 |
| **2** | [🎬 frontend/demo.html](frontend/demo.html) | 라이브 BEV 데모 — 운영자 콘솔 + 시민 앱 | 2분 |
| **3** | [📈 frontend/pitch.html](frontend/pitch.html) | 투자 피치덱 — ROI 347x · 사회적 가치 1,393억/년 · BM | 3분 |
| **4** | [🎯 docs/SUBMISSION_INDEX.md](docs/SUBMISSION_INDEX.md) | 평가 기준 ↔ 산출물 ↔ CI 가드 자가 점수표 (1차 105점 + 2차 100점) | 3분 |
| **5** | [💬 docs/QA_PREPARATION.md](docs/QA_PREPARATION.md) | 예상 Q&A 18개 + 30초 자기 소개 (5개 카테고리) | 5분 |

**추가 문서 (운영·장애 대응)**: [📕 docs/RUNBOOK.md](docs/RUNBOOK.md) — 9가지 시나리오 1줄 복구 · [📖 docs/PROPOSAL.md](docs/PROPOSAL.md) — 상세 제안서 v3

---

## 개요

기존 공공 CCTV에 SW만 추가(별도 하드웨어 0원)해 CV BEV로 칸별 점유를 실시간 추출하고, 10개 공공 API(날씨·문화행사·대기질·인구·엘리베이터 등)와 결합해 인사이트로 전환한다.

**핵심 KPI**

- 순 사회적 가치 **1,393억/년** (Monte Carlo 95% CI [1,064~1,808억])
- ROI **347x** · 절감 시간 473.4M분/년
- 2호선 단독 ROI **708x** · 157M분 절감

---

## 빠른 시작

```bash
git clone https://github.com/leelang7/MetroEyes.git && cd MetroEyes
pip install -r requirements.txt

# CV 모델 없이 fake BEV로 데모
python -m src.cv.lite_server --port 8765 --demo
```

```bash
# 또는 Docker
docker compose up -d   # backend :8765 + frontend :5173
```

화면:
- 운영자 콘솔: `http://localhost:5173/operator_web/index.html`
- 운영자 3D BEV: `http://localhost:5173/operator_web/realbev.html`
- 시민 PWA: `http://localhost:5173/passenger_app/index.html`
- 버스 콘솔: `http://localhost:5173/operator_web/bus.html`

---

## 실 카메라 파이프라인

```bash
# 호모그래피 캘리브레이션 (최초 1회)
python -m src.cv.calibrate --cam ceiling --source 0

# 백엔드 (YOLO11 + BoT-SORT + WebSocket :8765)
python -m src.cv.tesla_bev --port 8765 --model yolo11s.pt --imgsz 1280 --conf 0.18

# 비디오 피더
python scripts/feed_video.py path/to/clip.mp4
```

---

## 주요 기능

| 기능 | 설명 |
|---|---|
| **칸별 점유 BEV** | YOLO11+BoT-SORT+호모그래피 — 위에서 본 시점 익명 점 카운트 |
| **4단 차등 보상** | OD·환승·핫스팟 3축 교차로 ₩100~400 자동 산출 |
| **운영자 알람 4종** | 응급·분실물·우선석·병목 — 개인정보 Zero |
| **군중 밀집 사전 경고** | 밀도+속도(0.3m/s)+지속(45초) 3축 동시 검출 |
| **버스 통합** | 버스 칸별 BEV + 24시간 sparkline 점유 분석 |
| **시민 앱** | GPS 역 자동 매칭 · 5중 도착 알림 · 4언어 |
| **Flutter 네이티브** | Android / Windows / Web 크로스 플랫폼 |

---

## 데이터 출처

**서울 열린데이터광장**

| 데이터셋 | 분야 |
|---|---|
| 서울 실시간 도시데이터 (citydata) | 날씨·인구·도로·문화 복합 |
| 서울시 실시간 생활인구 (citydata_ppltn) | 인구 |
| 서울시 지하철 실시간 도착정보 | 교통 |
| 서울시 교통카드 지하철 시간대별 이용현황 | 교통 |
| 서울시 지하철역별 승하차 인원 정보 | 교통 |
| 서울시 자치구 시간별 대기환경 현황 | 환경 |
| 서울시 공공서비스예약 문화체험 정보 | 문화 |

**공공데이터포털**

| 데이터셋 |
|---|
| 서울교통공사_지하역사 실내 공기질 측정정보 |
| 서울교통공사_역사 엘리베이터 운행현황 |
| 국토교통부 버스 노선 정보 조회 서비스 |
| 국토교통부 버스 정류장 정보 조회 서비스 |

API 키: [data.seoul.go.kr](https://data.seoul.go.kr) 에서 발급 후 `.env`에 저장.

---

## REST API v1

백엔드(`lite_server.py`)가 13개 엔드포인트 제공 — 모두 CORS 허용.

| Endpoint | 설명 |
|---|---|
| `GET /health` | 시스템 상태 |
| `GET /api/v1/roi_curve` | ROI 곡선 (0~80%, 81 샘플) |
| `GET /api/v1/impact` | 누적 분산 임팩트 + tier 카운트 |
| `GET /api/v1/incidents` | 사고 6종 카운트 + 30건 이벤트 |
| `GET /api/v1/dispersion` | 분산 효과 검증 + 라이브 응답률 |
| `GET /api/v1/od_asymmetry` | 현 시각 OD 우선 역 TOP 5 |
| `GET /api/v1/transfer_priority` | 환승역 비대칭 TOP 5 |
| `GET /api/v1/policy_summary` | 정책 정의 + 라이브 통합 |
| `GET /api/v1/indoor_air` | 역사 실내 CO₂/PM2.5 |
| `GET /api/v1/elevator` | 승강기 운행 상태 |
| `GET /api/v1/occupancy_forecast` | 24시간 혼잡도 예측 |
| `GET /api/openapi.yaml` | OpenAPI 3.0 spec |
| `GET /api/docs` | 자동 HTML 명세 |

---

## 디렉토리 구조

```
.
├── src/
│   ├── cv/                # YOLO11 + BoT-SORT + BEV 파이프라인
│   ├── data_pipeline/     # 서울 공공 API 클라이언트
│   ├── models/            # 점유율 예측 모델 (LightGBM)
│   └── api/               # FastAPI + WebSocket 백엔드
├── frontend/
│   ├── operator_web/      # 운영자 대시보드 (지하철·버스·광고)
│   ├── passenger_app/     # 시민 PWA (4언어)
│   └── onepager.html      # A4 1-Pager
├── mobile_app/            # Flutter 네이티브 앱
├── docs/                  # 기획서·RUNBOOK·API 명세
├── scripts/               # 학습·캡처·데모 CLI
└── tests/                 # pytest 844 회귀 가드
```

---

## ML 모델 학습

```bash
python scripts/cluster_stations.py          # 역 클러스터 (K=3)
python scripts/train_occupancy.py --month 202602
```

→ `outputs/models/occupancy_lgbm.joblib` 생성. 백엔드가 lazy load해 `predict_occupancy` WS 응답.

---

## 자동 543 사이클 누적 (D-1, 마감 2026-05-13)

- ✅ **양면 가치 사슬 8단계** (CV → 도시 → 의사결정 → OD매칭 → 환승매칭 → 시민 차등 → 백엔드 자동보너스 → ROI 라이브)
- ✅ **데모 fail-safe 8중 구조**: `--demo` + 30초 인젝터 + 5분 sticky bar + 백엔드 join 요약 + 관리자 클릭 + warm seed + Docker compose + GitHub Actions CI
- ✅ **4언어** (ko/en/zh/ja) **11페이지 패리티** + Web Speech + ARIA + **5페이지 외국인 환영 토스트**
- ✅ **3개 EDA 실데이터 검증**: GBR R²=0.931 / 분산 효과 (σ −9% / 피크 −13.5%) / OD 비대칭 (삼성역 12x) / 환승 (충무로 +1.56)
- ✅ **CI 15 jobs + 844 pytest 회귀 가드** (cycle 318-543): OpenAPI(4) + ROI v3(5) + 분산(6) + OD/환승(6) + 보너스(6) + 그림(3) + 피치(6) + 임팩트(5) + cycle 356-543 신규 491 — 광고 KPI ↔ 코드 ↔ 그림 ↔ 덱 ↔ canonical JSON 자동 동기화
- ✅ **canonical KPI drift 자동 차단** (cycle 375): 1,393억 / 347x / 2호선 157M / CI [1,064~1,808] 전 산출물 동시 일치
- ✅ **제출 ship-gate** (cycle 380): `python scripts/submission_check.py --ci` 1초 12항목 PASS/WARN/FAIL — 매 푸시 자동 검증

---

## License

Apache 2.0 — [LICENSE](LICENSE)
