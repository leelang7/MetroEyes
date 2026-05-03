# MetroEyes

> *"테슬라가 도로를 BEV로 보듯, MetroEyes는 도시 교통 전체를 본다."*

**4중 데이터 융합** + **자체 CV** + **시민/운영자 듀얼 도메인** — 지하철·버스 둘 다, 시민의 한 번의 탑승 결정을 더 정확하게.

> 코드/디렉토리는 `subwaybev_*` 식별자를 보존 — 빌드 호환 유지. UI 표시만 MetroEyes.

## 라이브 데모 (3분)

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
| 서울 실시간 도시데이터 (POI 인구·혼잡도) | `citydata_ppltn` | 역세권 컨텍스트 |
| 자치구 일별 생활인구 | `SPOP_DAILYSUM_JACHI` | 일별 트렌드 |
| 시간대별 승하차 (CardSubway) | `CardSubwayStatsNew` | ML 학습 입력 |
| 도시철도 실시간 도착 (TOPIS) | `realtimeStationArrival` | 도착 ETA |

키는 [data.seoul.go.kr](https://data.seoul.go.kr) 마이페이지에서 발급 후 `.env`의 `SEOUL_OPENDATA_API_KEY`에 저장.

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

## License

내부 개발 — 외부 공개 미정.
