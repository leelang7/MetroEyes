# MetroEyes — 실행 명령어 (운영 + 시연)

> 이 문서 한 번 읽고 그대로 복붙하면 끝. 모든 명령은 PowerShell 기준.

---

## 1. 라이브 데모 한 번에 띄우기 (콘솔 안 뜸 — 권장)

**`start_silent.vbs` 더블클릭** — cmd/PowerShell 창 한 개도 안 뜨고 4개 detached process가 hidden으로 시작:
- backend (`pythonw.exe` YOLO + WebSocket :8765)
- publisher (`pythonw.exe` vtest.avi 송출)
- ngrok :4040 (외부 wss 노출)
- 정적 파일 서버 :5173

로그는 `logs/backend.log` / `logs/publisher.log` / `logs/ngrok.log` / `logs/static.log`에 기록.

**검증**: `http://localhost:5173/frontend/operator_web/realbev.html` 열면 LIVE.

---

## 2. 종료 (콘솔 안 뜸)

**`stop_silent.vbs` 더블클릭** — 모든 pythonw + ngrok 즉시 종료.

---

## 1-옵션. 콘솔 minimize로 띄우기 (디버깅 시)

```powershell
cd C:\Users\leesc\Documents\Seoul
.\start_demo.bat                # 4개 콘솔 minimize (작업표시줄)
.\stop_demo.bat                 # 종료
```

또는 PowerShell:
```powershell
.\scripts\start_demo.ps1 -IncludeStatic        # minimize
.\scripts\start_demo.ps1 -IncludeStatic -Visible  # 콘솔 보이게 (yolo 로딩 진행 직접 봐야 할 때)
.\scripts\start_demo.ps1 -Stop
```

---

## 3. 외부 시연 (영구 고정 URL)

backend + ngrok만 살아있으면 누구든 접속 가능:

| URL | 화면 |
|---|---|
| **https://leelang7.github.io/MetroEyes/** | 메인 진입 (4 화면 카드) |
| https://leelang7.github.io/MetroEyes/frontend/operator_web/realbev.html | 운영자 3D BEV (메인 wow) |
| https://leelang7.github.io/MetroEyes/frontend/operator_web/index.html | 운영자 지하철 |
| https://leelang7.github.io/MetroEyes/frontend/operator_web/bus.html | 운영자 버스 |
| https://leelang7.github.io/MetroEyes/frontend/passenger_app/index.html | 시민 PWA |

GitHub Pages → `wss://rebekah-derisible-tanisha.ngrok-free.dev` 자동 연결. 너 PC 켜놓는 한 LIVE.

---

## 4. 개별 컴포넌트 직접 띄우기

### 4.1 백엔드만

```powershell
cd C:\Users\leesc\Documents\Seoul
.\.venv\Scripts\python.exe -u -m src.cv.tesla_bev --port 8765 --model yolo11s.pt --imgsz 1280 --conf 0.18
```

콘솔에 `[i] BEV multi-class ... ws://0.0.0.0:8765` 떠야 정상.

### 4.2 영상 publisher (vtest.avi 송출)

```powershell
cd C:\Users\leesc\Documents\Seoul
.\.venv\Scripts\python.exe scripts\feed_video.py
```

다른 영상으로:
```powershell
.\.venv\Scripts\python.exe scripts\feed_video.py path\to\clip.mp4
```

### 4.3 ngrok (외부 노출)

```powershell
ngrok http 8765
```

reserved domain (영구 고정) 사용 — 너 ngrok 무료 계정에 이미 등록된 `rebekah-derisible-tanisha.ngrok-free.dev` 자동.

### 4.4 정적 파일 서버

```powershell
cd C:\Users\leesc\Documents\Seoul
.\.venv\Scripts\python.exe -m http.server 5173
```

→ `http://localhost:5173/frontend/...` 접근.

---

## 5. ML 점유율 모델 학습 (한 번)

```powershell
cd C:\Users\leesc\Documents\Seoul
.\.venv\Scripts\python.exe scripts\cluster_stations.py        # 역 클러스터 (먼저 1회)
.\.venv\Scripts\python.exe scripts\train_occupancy.py --month 202602
```

**산출**:
- `outputs/models/occupancy_lgbm.joblib` — 학습 모델
- `outputs/occupancy_metrics.json` — MAE/RMSE/R²
- `outputs/figs/20_occupancy_pred_vs_true.png` — 검증 산점도
- `outputs/figs/21_occupancy_feature_importance.png`

backend 다음 재시작부터 lazy load → 운영자 콘솔 metrics 카드 자동 점등.

---

## 6. 데모 자동 캡처 (PNG / WebM)

```powershell
cd C:\Users\leesc\Documents\Seoul
.\.venv\Scripts\python.exe scripts\capture_demo.py            # PNG 4장
.\.venv\Scripts\python.exe scripts\capture_demo.py --record   # + 운영자 30초 webm
```

**산출**: `outputs/demo/operator_realbev.png`, `operator_index.png`, `operator_bus.png`, `citizen_pwa.png` + (옵션) `operator_realbev.webm`

---

## 7. Flutter 폰 앱 빌드 + 설치

```powershell
cd C:\Users\leesc\Documents\Seoul\mobile_app
flutter build apk --debug
adb install -r build\app\outputs\flutter-apk\app-debug.apk
```

USB 연결된 안드로이드 폰에 설치 + 자동 LIVE 연결 (ngrok 영구 도메인).

---

## 8. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| 운영자 콘솔 "연결 실패" | backend 죽음 | 4.1 다시 / `.\start_demo.bat` |
| 폰 앱 "SubwayBEV" 헤더 | 옛 빌드 | 7번 다시 빌드/설치 |
| 영상 변경 시 "재생 실패" | `frontend/videos/*.mp4` 누락 | git pull 또는 `frontend/videos/` 디렉토리 확인 |
| ngrok ERR_NGROK_6030 | tunnel hang | ngrok 프로세스 kill 후 재기동 |
| ML 메트릭 카드 안 보임 | 모델 미학습 | 5번 학습 후 backend 재시작 |
| 정적 페이지 외부에서 안 보임 | GitHub Pages 미설정 | repo Settings → Pages → Source = GitHub Actions |

---

## 9. Cloudflare named tunnel — 영구 고정 도메인

ngrok abuse interstitial 우회 + URL 절대 안 바뀜.

**1회 setup**:
```powershell
# 0) cloudflared 설치 (1회)
winget install Cloudflare.cloudflared

# 1) Cloudflare 계정 + 도메인 등록 (한 번만)
#    https://dash.cloudflare.com → Add a site → 도메인 입력
#    Cloudflare Registrar에서 새로 사도 됨 ($10~/년)

# 2) tunnel + DNS 자동 setup
.\scripts\setup_cloudflared.ps1 -Domain app.YOUR-DOMAIN

# 3) frontend wss URL 교체 + push
#    frontend/operator_web/*.html, frontend/passenger_app/*.html 5 파일의
#    'wss://...trycloudflare.com' (또는 ngrok) → 'wss://app.YOUR-DOMAIN' 일괄 교체
git commit -am "feat: switch to permanent cloudflare domain" && git push
```

**일상 시작/종료**:
```powershell
# 백엔드 + publisher + 정적서버는 start_silent.vbs로 (cloudflared 제외)
# cloudflared는 별도 1회 시작 (한 번 띄워두면 PC 재부팅 전까지 동작):
cloudflared tunnel --config cloudflared-config.yml run metroeyes
```

자동 시작 (Windows 부팅 시) 원하면:
```powershell
cloudflared service install --config "C:\Users\leesc\Documents\Seoul\cloudflared-config.yml"
```

## 10. 환경 변수 (`.env`)

```bash
# 일반 데이터 (citydata, CardSubway, 행사 등)
SEOUL_OPENDATA_API_KEY=...

# 도시철도 실시간 도착 (TOPIS swopenapi) — 별도 신청 키
SEOUL_SUBWAY_ARRIVAL_KEY=...

# 버스 도착 (있으면) — 공공데이터포털
SEOUL_BUS_ARRIVAL_KEY=...
```

키 발급: https://data.seoul.go.kr 마이페이지 → 인증키 관리.
