# MetroEyes RUNBOOK — 장애 시나리오 + 1줄 복구 (cycle 376)

> 본선 발표 (2026-07-06) · 평가 시연 중 장애 발생 시 1줄 명령으로 복구.
> 8단 fail-safe 가 이미 backend / frontend / CI 에 빌트인 — 모든 장애가 자동 처리됨.
> 이 문서는 *수동 개입* 이 필요한 잔여 케이스만 다룸.

---

## 1. 백엔드 죽음 — `lite_server.py` 또는 `tesla_bev.py` 충돌

### 진단
```powershell
# Status 확인
curl http://localhost:8765/health | jq '.api'
# OR (tesla_bev 실행 중일 때만)
Get-Process | Where-Object { $_.ProcessName -like '*python*' }
```

### 복구 (1줄)
```powershell
# 가장 빠름 — start.bat 자동 재시작
.\start.bat

# OR 수동 lite-mode (CV 안 켜짐, BEV demo broadcast)
python -m src.cv.lite_server --port 8765 --demo
```

**Recovery time**: 5초 (--demo) ~ 30초 (full CV)
**Fallback**: 시민 PWA / 운영자 콘솔 모두 자동 reconnect (5초 grace + 30초 ping)

### 사고 사례
- cycle 339: ultralytics 미설치 → start.bat 가 자동 lite 폴백
- cycle 342: websockets 16 process_request API 변경 → wrapper 자동 적응 (수정 완료)

---

## 2. Cloudflare 터널 끊김 — `app.allthatai.kr` 응답 없음

### 진단
```powershell
curl https://app.allthatai.kr/health
# 또는 tunnel 프로세스
Get-Process cloudflared -ErrorAction SilentlyContinue
```

### 복구 (1줄)
```powershell
# start_demo.ps1 가 자동 hidden Start-Process 로 재시작
.\start_demo.ps1

# OR 수동
& "$env:USERPROFILE\.cloudflared\cloudflared.exe" tunnel --config "$pwd\cloudflared-config.yml" run
```

**Recovery time**: 10초
**Fallback**: GitHub Pages (https://leelang7.github.io/MetroEyes/) 가 정적 자료 + ngrok 라이브 자동 분기

### 사고 사례
- cycle 338: child PowerShell 종료 → hidden Start-Process 로 안정화
- 2026-05-08: status.cloudflare.com global outage → GitHub Pages fallback 자동 동작

---

## 3. GPS 안 잡힘 — 시민 PWA 자동 매칭 실패

### 사용자 증상
> "GPS 권한은 줬는데 역이 잘못 매칭됐어요"

### 복구 (시민 직접)
1. PWA 헤더 `🚇 잠실역` 박스 클릭 → 역 picker 모달 오픈
2. 호선 chip 필터 선택 (1호/2호/.../9호/💰 보너스)
3. 검색창에 역 이름 직접 입력 (4언어 검색 OK)
4. 또는 모달 하단 `📍 현재 위치 다시 잡기` 버튼

**Fallback**: 수동 선택은 GPS 우회. 보너스 chip 으로 OD/환승 즉시 확인 가능.

---

## 4. LLM API 한도 초과 — Claude Haiku 응답 없음

### 진단
```python
# 백엔드 로그에서 ANTHROPIC_API_KEY 관련 에러 확인
# tesla_bev.py 의 fetch_context_news() 가 Naver 뉴스 fallback 됨
```

### 복구
- **자동 fallback**: Claude API 실패 시 Naver 뉴스 첫 항목 title (60자) 그대로 broadcast
- **수동 복구**: 환경변수 `ANTHROPIC_API_KEY` 갱신 후 백엔드 재시작
- **무복구**: LLM 컨텍스트 카드만 hidden — 다른 기능 정상

**ad_pricing.html 의 LLM 카드**: 30분 캐시 (localStorage) — API down 시 직전 컨텍스트 유지.

---

## 5. WebSocket 끊김 — 시민 폰 깜빡거림

### 사용자 증상
> "시민앱이 계속 ON/OFF 깜빡거려요"

### 자동 복구 (cycle 340)
- **5초 offline grace**: 즉시 offline 표시 안 함 (네트워크 일시 끊김 흡수)
- **30초 ping keepalive**: WebSocket alive 보장
- **1.5~4.5초 jitter reconnect**: 동시 재연결 폭주 방지

### 수동 복구
- 시민: 앱 닫고 다시 열기
- 운영자: backend 재시작 → 5초 후 모든 client auto-reconnect

---

## 6. 발표 시연 중 backend down — Demo fail-safe 8단

데모 진행 중 backend 가 죽어도 시연 끊기지 않도록 8 단 방어:

| 단계 | 메커니즘 | 효과 |
|---|---|---|
| 1 | `--demo` 모드 (CV 모델 미설치 OK) | 5Hz fake BEV broadcast |
| 2 | 30초 incident injector | 자동 incident 생성 → KPI live |
| 3 | 5분 sticky bar | 마지막 incident 5분 유지 |
| 4 | backend join summary | 새 client 연결 시 누적 KPI 즉시 푸쉬 |
| 5 | admin 클릭 시연 mode | `▶︎ 시연` 버튼 즉시 30초 incident |
| 6 | warm seed 12건 | 기동 즉시 KPI 0 → 12 |
| 7 | Docker compose | `docker compose up -d` 1줄 |
| 8 | GitHub Actions CI | push 자동 검증 → 깨진 코드 main 진입 차단 |

---

## 7. 자동 회귀 검출 — KPI drift 자동 차단 (cycle 375)

CI 가 매 push 마다 검증:
- 광고 KPI 1,393억 / 347x / 2호선 157M ↔ pitch / onepager / SLIDES / PROPOSAL 동시 일치
- 불일치 시 즉시 fail → main 진입 차단

```powershell
# 로컬 사전 검증
python scripts/submission_check.py
# Exit 0=PASS / 1=WARN / 2=FAIL
```

**제출 직전 (D-day) 필수 1줄**: `python scripts/submission_check.py`

---

## 8. 메인 도메인 down — `leelang7.github.io` 접속 불가

### 진단
- GitHub Pages 상태: https://www.githubstatus.com/
- 평소 응답: 200 OK + `frontend/index.html`

### 복구
- GitHub Pages 는 SLA 99.9% — 5분 내 자동 복구가 일반적
- 임시 우회: 로컬 `python -m http.server 5173` 후 `localhost:5173/frontend/index.html`
- 평가위원에게는 GitHub repo URL `https://github.com/leelang7/MetroEyes` 도 함께 안내

---

## 9. 평가 시연 직전 체크리스트 (5분 전)

**1줄 통합 검증 (cycle 395 + 412 + 419 — 권장)**:
```powershell
# Windows PowerShell
.\scripts\dday.ps1 -Quick    # 빠른 검증 (10초)
.\scripts\dday.ps1 -Full     # 풀 검증 (~3분, D-1 권장)
.\scripts\dday.ps1 -Regen    # EDA 재생성만
```
```bash
# Mac/Linux bash (cycle 412 mirror)
./scripts/dday.sh --quick    # 동일 동작
./scripts/dday.sh --full
./scripts/dday.sh --regen
```
```bash
# Make (cycle 419 — third-platform parity)
make verify                  # quick (alias for `make`)
make full                    # EDA 재생성 + 풀 ship-gate
make regen                   # EDA 4 scripts only
make install                 # 첫 셋업 (cycle 421 — pip install)
make test                    # pytest 246+ 가드만
make demo                    # backend lite-server --demo
make help                    # 모든 target 설명
```

**개별 명령** (수동 디버깅 시):
```powershell
# 1. 백엔드 자가 진단
curl http://localhost:8765/health | jq

# 2. canonical KPI ↔ 광고 자료 정합 (cycle 375)
python -m pytest tests/test_kpi_drift.py -v

# 3. 전체 회귀 통과
python -m pytest tests/ --ignore=tests/test_smoke.py -q

# 4. 제출 직전 자동 검증 (12 항목)
python scripts/submission_check.py
```

기대값: 216+ passed · submission_check PASS

---

## 사고 대응 연락

- **개발자**: 이상철 · leescvsir@gmail.com
- **GitHub Issues**: https://github.com/leelang7/MetroEyes/issues
- **공지**: 본선 평가 직전 1시간에는 새 commit 금지 (회귀 위험)
