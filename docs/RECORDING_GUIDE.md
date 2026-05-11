# 발표 영상 5분 풀 캡처 가이드

> 우선순위 #6 — 자동 모드로 자동화 불가능, 사용자가 직접 캡처.
> 현재 누적 산출(D-2, v6.11 — 496 사이클, IDEA-7/8/9 + 5중 모달리티 + 6단 견고화 + CI 15 jobs / 389 회귀 가드 + canonical KPI drift 자동 차단 + admin 시민신고 LIVE 패널 + 8-Moat + FAB 상태 머신) 모두 활용 가능.

## 사전 준비

### 1. 환경 점검
```powershell
# backend --demo 모드 시작 (CV 모델 없이도 BEV broadcast)
python -m src.cv.lite_server --port 8765 --demo

# warm seed 12건 + 5분마다 자동 incident → 시작 즉시 KPI 라이브
```

### 2. 브라우저 준비
- **Chrome 권장** (Web Speech API + WebSocket + Service Worker 모두 호환)
- **창 크기**: 1920×1080 (4-패널 demo.html 가독성)
- **localStorage 클리어** (환영 toast 첫 노출 보장):
  - DevTools (F12) → Application → Storage → Clear site data

### 3. 화면 녹화 도구
- **OBS Studio** (무료, Windows/Mac/Linux 모두): Display Capture or Window Capture
- **ShareX** (Windows): Ctrl+Shift+Q (영역 선택 → mp4)
- **macOS**: Cmd+Shift+5 → 영역 녹화

### 4. 마이크 (옵션)
- 내레이션 추가 시 **Audacity** 별도 녹음 → 후편집에서 합치기 (영상 품질 ↑)
- 또는 OBS에서 마이크 직접 녹음

## 5분 시퀀스 (권장)

| 시각 | 화면 | 멘트 (한국어) | 핵심 |
|---|---|---|---|
| 0:00~0:30 | `index.html` 진입 허브 | "MetroEyes — 도시 교통 BEV 인사이트. 시민 분산 한 번이 ROI 347배 사회 가치" | 8 카드 허브 + 라이브 KPI |
| 0:30~1:00 | `pitch.html` 헤더 KPI + 슬라이더 | "응답률 슬라이더 30% 시 1,393억/년. 차등 보상 4단으로 우선 분산 가속" | 헤더 8개 KPI + ±15% CI band |
| 1:00~1:30 | `pitch.html` 그림 2,3 (분산 효과) | "실 데이터 28일 평균에서 σ −9% / 피크 −13.5% 검증" | 분산 EDA |
| 1:30~2:00 | `pitch.html` 그림 4,5 (OD/환승) | "삼성 OFF/ON 12배 출근 도착지 / 충무로 환승 비대칭 +1.56" | OD + 환승 EDA |
| 2:00~2:30 | `pitch.html` 차등 보상 표 | "₩100 → ₩200 → ₩300 (OD) → ₩400 (환승). backend 자동 가산" | 4단 차등 + 그림 4·5 매핑 |
| 2:30~3:00 | `demo.html` ▶︎ 시연 시작 | "5분 통합 시연 — 4 패널 동시 + 자동 시퀀스" | 4 panel demo |
| 3:00~3:30 | 운영자 콘솔 헤더 | "분산 효과 σ / 피크 / tier 분포 / OD 우선 / 환승 흐름 5 chip 라이브" | 운영자 4 페이지 |
| 3:30~4:00 | 시민 PWA | "GPS 자동 매칭 + 환영 toast 4언어 + 차등 보상 chip ₩300/₩400" | 외국인 친화 |
| 4:00~4:30 | `realbev.html` 비상 동선 클릭 | "K-means(K=4) + 헝가리안 1:1 매칭. 단일 출구 대비 cost N% 절감" | A*+K-means |
| 4:30~5:00 | `admin.html` Debug Console | "13 endpoint REST + 시민신고 LIVE + tier_counts 분포 + OD/환승 카드 라이브" | 백엔드 가시화 |

## 후편집

### OBS 권장 설정
- **Format**: mp4 (H.264, AAC)
- **Bitrate**: 5,000~8,000 kbps (1080p)
- **fps**: 30 (시연 충분)
- **Encoder**: x264 (CPU) 또는 NVENC (GPU)

### 자막 (옵션)
- 한글 캡션은 발표 시 평가위원에게 도움이 됨 → DaVinci Resolve / CapCut 무료
- 핵심 KPI 숫자는 강조 (1,393억 / 347x / σ −9% / 충무로 +1.56)

### 썸네일 (제출용)
- **권장**: `frontend/pitch.html` 헤더 KPI 가 보이는 첫 화면
- 또는 `figs/dispersion_sim.png` 또는 `figs/od_asymmetry.png` 직접 활용

## 확인 사항

- ✅ 누적 카운터가 0이 아닌지 (warm seed 12건 + 자동 누적)
- ✅ tier_counts 분포 막대가 보이는지 (`--demo` 가중치 보정으로 자동)
- ✅ 모든 chip이 hidden 해제됐는지 (8s/12s/60s 폴링 후 표시)
- ✅ 환영 toast 4언어 노출 (localStorage 클리어 후 첫 진입)
- ✅ pitch.html PDF 인쇄 — 결과를 PDF로 동시 첨부 (정적 백업)

## 영상 검증 체크리스트

- [ ] 1080p 해상도 + 30fps 이상
- [ ] 마이크 음량 적절 (-6dB ~ -3dB)
- [ ] 5분 정확 (4:50~5:10 허용)
- [ ] 한국어 내레이션 자연스러움
- [ ] 핵심 KPI 자막/강조
- [ ] BGM 없음 (또는 저작권 free 30dB 이하 BGM)

## 제출 (5/13 마감)

영상 파일명: `이석창_MetroEyes_시연영상.mp4`
크기 권장: 100MB 이하 (메일 첨부 가능 범위) — 더 크면 GitHub Releases 또는 마이박스 링크.
