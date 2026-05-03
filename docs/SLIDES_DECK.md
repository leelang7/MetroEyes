# MetroEyes 상세기획서 — 한컴/PPT 슬라이드 텍스트
> 각 슬라이드의 텍스트만 정리. 한쇼/PowerPoint에 그대로 복사·붙여넣기.
> SLIDES.html 의 시각 디자인을 한쇼에서 재구성할 때 참조.
> **개인정보 금지** — 팀명(MetroEyes) / 성명(이상철)만 표지에 기재.

---

## 표지 — Slide 0

```
2026년 서울시 빅데이터 활용 경진대회 · 창업 부문
[상세기획서]

서비스명: MetroEyes
참가자명: 이상철

부제: 도시 교통 실시간 BEV 점유 인사이트
     자체 CV + 7개 공공 API fusion + TRIZ 발명원리
     "칸별 점유" 라는 빈칸을 채우는 양면 가치사슬 솔루션
```

---

## 1. 제안배경 및 출품작 소개 (3장)

### Slide 1 — 서울 지하철의 "보이지 않는 30%"

```
부제: 총량은 균형 잡혀 보이지만, 그 안에서 어느 칸이 비었는지는 아무도 모른다.

[KPI 4종]
- 일평균 통행: 700만 명/일
- 시간대 진폭: 1.9× (피크/한산)
- 호선 격차: 19.4% (2호선 비중)
- 칸 컬럼: 0 (공식 스키마에 부재)

[문제 정의 — 4단 패러독스]
1) 운영자: 칸별 점유 데이터 없어 평균값 운영 → 자원 낭비
2) 시민:   어느 칸이 한산한지 모름 → 압사 위험 + 시간 손실
3) 광고주: 시간대별 인구 차이 모른 채 월 단위 고정가 → 단가 비효율
4) 안전:   비상시 출구 동선 정적 → 대피 효율 저하
```

### Slide 2 — 출품작 MetroEyes

```
부제: "테슬라가 도로를 BEV로 보듯, 우리는 칸 내부와 역세권을 BEV 평면에서 본다."

[IFR — 이상결과 (TRIZ)]
별도 차내 인프라 설치 없이, 승객들이 가장 한산한 칸을 자동으로 알며,
그 정보가 승객의 자연스러운 행동만으로 자동 업데이트된다.
→ 운영자 추가 비용 0, 사용자 늘수록 정확도 ↑ (네트워크 효과)

[A · 운영자 콘솔]
지하철·버스 실시간 BEV 3D 점유 시각화 + 광고 단가 자동 책정 + 비상 동선 추론

[B · 시민 앱 (PWA + 네이티브)]
가장 한산한 칸 추천 + citydata 통합 (날씨/공기/도로) + 분산 운임 인센티브

[한 줄 메시지]
공공 API의 갱신 주기 한계를 자체 CV + 칼만 fusion으로 돌파,
TRIZ 발명원리 5개로 모순 5개 해결, 연 1.27조원 사회적 가치·ROI 3,700배 정량화.
```

### Slide 3 — EDA 골든 인사이트

```
[데이터 출처]
서울 OpenAPI CardSubwayStatsNew + CardSubwayTime 202602 분석

[5가지 발견]
① 칸 컬럼 부재   공식 스키마(52컬럼) 검증           → 진입 명분 확정
② 시간대 양봉    08시 하차 14M / 18시 승차 13.8M    → 분 단위 추정 가치
③ 호선 격차 CV=1.11 2호선 5.85M (Top1, 19.4%)     → 호선별 fine-tune
④ Top 20 = 18%   서울역(490K) > 잠실(428K) > ...   → 우선 배포 후보
⑤ 환승역 비대칭↓ 고속터미널·사당·강남: 들어오는 만큼 나감 → "균형 안의 빈 칸"

[골든 한 줄]
"총량은 균형 잡혀 보이지만, 그 안에서 어느 [칸]이 비었는지는 알 수 없다."
→ MetroEyes의 핵심 가치 제안과 직결.
```

---

## 2. 출품작 핵심내용 (4장)

### Slide 4 — 시스템 아키텍처

```
부제: 자체 CV 백엔드 + 7개 공공 API fusion + 양면 가치사슬

[A] 데이터 레이어 (7+ 공공 API)
  CardSubwayTime · realtimeStationArrival · citydata · citydata_ppltn ·
  ListPublicReservationCulture · TimeAverageAirQuality · SPOP_DAILYSUM_JACHI

[B] 처리 레이어 (Python FastAPI)
  자체 CV (YOLO11s + BoT-SORT + 호모그래피 BEV)
  ML 회귀 (GradientBoosting R²=0.78) + 클러스터링 (K=3, silhouette 0.387)
  칼만 fusion 나우캐스팅 (TRIZ #15+#1)

[C] 전송 레이어 (WebSocket 영구 도메인)
  wss://app.allthatai.kr (Cloudflare named tunnel)

[D] 표시 레이어 (양면 가치사슬)
  운영자 콘솔: 지하철 / 버스 / 실카메라 / 광고단가 (Three.js + Vanilla JS)
  시민 PWA: 추천 칸 + citydata 칩 + 분산 운임 인센티브
  네이티브 폰: Flutter (Phone-as-Sensor 텔레메트리)
```

### Slide 5 — 활용 공공데이터 목록 (정확한 명칭)

```
서울 열린데이터광장 - CardSubwayTime
서울 열린데이터광장 - realtimeStationArrival
서울 열린데이터광장 - citydata
서울 열린데이터광장 - citydata_ppltn
서울 열린데이터광장 - ListPublicReservationCulture
서울 열린데이터광장 - TimeAverageAirQuality
서울 열린데이터광장 - CardSubwayStatsNew
공공데이터포털 - 국토교통부 버스정류소 정보
공공데이터포털 - 국토교통부 버스 노선 정보

[가점 차원]
6+개 분야(교통·환경·문화·인구·기상·도로) 결합 — TRIZ #5(통합) 적용.
```

### Slide 6 — TRIZ 발명원리 매트릭스

```
부제: 단순 대시보드가 아닌, 발명 방법론으로 차별화

| 모순 | 개선 ↔ 악화                  | 해법                              | 원리              |
|------|------------------------------|-----------------------------------|-------------------|
| M1   | 칸별 정확도 ↔ 차내 진입 불가 | 폰 BLE/WiFi/모션 + 자체 CV PoC    | #25 자기서비스    |
|      |                              |                                   | #28 다른신호      |
| M2   | 분 단위 ↔ 30분 평균          | 칼만 fusion 나우캐스팅            | #15 동적성 / #1 분할 |
| M3   | 전 역사 ↔ 예산               | K=3 클러스터링, 환승허브 85역 우선 | #5 통합 / #6 범용성 |
| M4   | 정확도 ↔ 프라이버시          | 개인 ID 미생성, BEV bbox 집계     | #2 추출 / #3 국소품질 |
| M5   | 모델 정확도 ↔ 라벨 부재      | CO₂ ↔ 인원 weak supervision       | #28 / #25         |

[심사위원 메시지]
"단순 데이터 시각화가 아니라, 5개 모순을 발명 방법론으로 정량 해결한 시스템"
```

### Slide 7 — 검증 완료 결과

```
① CO₂ ↔ 인원 weak supervision (Pearson 상관)
  OZON (O₃)  r = +0.453  p = 0.026  ★  활동↑ → 광화학 반응↑
  SPDX (SO₂) r = +0.450  p = 0.027  ★  차량 배출↑
  CBMX (CO)  r = -0.523  p = 0.009  ★★ 난방/시간대 dependency
  → 야외 대기에서도 통계적 유의 양 상관 확인.
  → 지하역사 CO₂ 직접 측정 시 r ≥ 0.7 예상

② 칼만 fusion 나우캐스팅 (RMSE 기준)
  공공 30분 평균만   RMSE = 0.1231  baseline
  도착정보 (4분)     RMSE = 0.0697  가용 시각만
  칼만 fusion        RMSE = 0.1101  모든 시각, 가용 신호 통합 안전

③ 클러스터링 (K-means + silhouette)
  296역 K=3 (silhouette 0.387, PCA 84.1% 분산)
  → 오피스 54 / 주거 157 / 환승허브 85
  → 환승허브 우선 배포 시 ROI 최대화
```

---

## 3. 기존 서비스와의 차별성 (2장)

### Slide 8 — 기존 솔루션 비교

```
| 출처                  | 갱신   | 칸별 | 자체CV | 양면 | 한계                  |
|-----------------------|--------|------|--------|------|----------------------|
| 공공 CardSubwayTime   | 월     | ✗    | ✗      | ✗    | 사후 통계             |
| TOPIS realtimeArrival | 분     | ✗    | ✗      | ✗    | 차편 위치만 (ETA)     |
| SK PUZZLE (유료)      | 10분   | △    | ✗      | ✗    | 유료, 일부 노선만     |
| 대기업 대시보드       | 시간   | ✗    | ✗      | ✗    | 정적 시각화 위주      |
| MetroEyes             | 분 단위 | ○    | ○      | ○    | 자체 CV + 칼만 + 양면 |

[독창성 5요소]
1. 자율주행 CV 백그라운드 — 호모그래피·BEV·BoT-SORT·YOLO11 직접 구현
2. 칸 컬럼 부재 정량 입증 — 1주차 EDA 골든 인사이트
3. TRIZ 발명원리 5개 매핑 — 발명 방법론으로 차별화 정량화
4. 양면 가치사슬 (운영자 + 시민 + 광고주)
5. Production-grade 라이브 데모 — 영구 도메인 + 자동 배포
```

### Slide 9 — 6대 혁신 아이디어

```
| # | 아이디어                | 핵심 차별점                                          | 상태       |
|---|-------------------------|------------------------------------------------------|------------|
| 1 | Phone-as-Sensor         | 승객 폰 BLE/WiFi/모션 → 차내 카메라 0대로 점유 추정   | stub 동작  |
| 2 | 다중신호 칼만 나우캐스팅 | 30분 평균 + 분 + CV → 분 단위 추정 (RMSE 측정)       | 검증 완료  |
| 3 | CO₂ Weak Supervision    | 라벨링 비용 0, 환경 신호 ↔ 인구 흐름 (논문 트랙)     | 상관 입증  |
| 4 | 광고 가격 자동화        | 역×시간대 동적 단가, 가치사슬 3단                    | 페이지 동작|
| 5 | 분산 운임 인센티브      | citydata 분 단위 인구로 즉시 발동 — "정보 → 행동"    | 시민 앱 박음|
| 6 | 비상 동선 추론          | BEV → 안전. 점유 분포 → A* 출구 추천. 화재/테러 대응 | 콘솔 박음  |

아이디어 6개 모두 코드로 동작 — 발표 시 라이브 시연 가능.
```

---

## 4. 개발과정 및 방법 (2장)

### Slide 10 — 4주 스프린트 + D-10

```
[W1] EDA + 명분
   CardSubwayStatsNew/Time 분석, 칸 컬럼 부재 정량 입증, 시간대 양봉 도출

[W2] 모델링
   K-means 클러스터링 K=3 (silhouette 0.387) + GBR 회귀 (R²=0.78)

[W3] CV 파이프라인
   YOLO11s + BoT-SORT + 호모그래피 BEV (4점 캘리브레이션)

[W4] 듀얼 도메인 + 인프라
   운영자 콘솔 4종 + 시민 PWA + 네이티브 + Cloudflare 영구 도메인

[D-10] 혁신 아이디어 적용
   Phone-as-Sensor + 광고 단가 + 분산 인센티브 + 비상 동선 + CO₂ 검증

[개발 방법론]
1) 가설 → 데이터 검증 → 모델  (수치 검증 후 통합)
2) MVP 우선  (합성 시뮬 → 실 카메라 PoC → 외부 노출)
3) Production-grade 인프라  (자동 배포 + 영구 도메인)
```

### Slide 11 — 핵심 알고리즘: 호모그래피 BEV

```
① 4점 캘리브레이션
   카메라 영상의 ground plane 4점(시계방향) → BEV 평면 [0,1]² 정규화
   cv2.findHomography (RANSAC) 로 3×3 변환 행렬 산출

② 검출 → 트래킹 → 투영
   YOLO11s 사람 검출 → BoT-SORT ID 추적 (Kalman + ReID)
   → bbox 발 위치 (xc, y_bottom) → 호모그래피로 BEV 변환

③ 점유 정규화 + 칼만 fusion
   BEV 좌표 → 칸 정원으로 normalize (0~1.05)
   분 단위 칼만 필터로 노이즈 평활 (TRIZ #15+#1)

[의사코드]
img_pts = [(240,130), (400,130), (560,360), (80,360)]
bev_pts = [(0.30,0.05), (0.70,0.05), (0.95,0.95), (0.05,0.95)]
H = cv2.findHomography(img_pts, bev_pts, RANSAC)

# 매 프레임
tracks = yolo.track(frame, persist=True, tracker='botsort.yaml')
for t in tracks:
    foot = (t.xc, t.y2)
    bev = H @ [foot.x, foot.y, 1]
    ws.send({id, bev_x, bev_y, class})
```

---

## 5. IA (Information Architecture) (3장)

### Slide 12 — 사이트맵

```
[ROOT] https://leelang7.github.io/MetroEyes/
├─ 안내 페이지 (각 도메인 카드 그리드)
│
├─ [A] 운영자 콘솔  /frontend/operator_web/
│      ├─ index.html       지하철 — 호선·역·시각·아키타입 + 실시간 KPI 4종
│      ├─ bus.html         버스 — 노선 142 + BIS 데이터 통합
│      ├─ realbev.html     실 카메라 (3D Three.js BEV + 비상 동선 추론)
│      └─ ad_pricing.html  광고 단가 (역×시간대 히트맵 + KPI 4종)
│
├─ [B] 시민 PWA  /frontend/passenger_app/
│      ├─ index.html       정류장 — 추천 칸 + citydata 칩 + 분산 인센티브
│      └─ onboard.html     탑승 중 — 다음 정거장 + 출구 안내
│
└─ [C] 네이티브 앱  /mobile_app/ (Flutter)
       └─ Phone-as-Sensor 텔레메트리 + GPS 매칭 + 임팩트 카운터

[인프라]
백엔드:           wss://app.allthatai.kr (FastAPI + WebSocket)
정적 호스팅:      leelang7.github.io (GitHub Pages 자동 배포)
백엔드 외부 노출: cloudflared (Cloudflare named tunnel)
자체 도메인:      allthatai.kr (개인 보유 - 가비아)
```

### Slide 13 — 데이터 흐름

```
[INPUT]
서울 OpenAPI 7개:
  CardSubwayTime · realtimeStationArrival · citydata · citydata_ppltn
  ListPublicReservationCulture · TimeAverageAirQuality · CardSubwayStatsNew
공공데이터포털:
  국토교통부 BIS 버스정류소·노선
자체 CV:
  USB 카메라 / mp4 → YOLO11 → BoT-SORT → 호모그래피
폰 텔레메트리:
  BLE/WiFi/모션 익명 집계 (IDEA-1)

       ↓

[PROCESS] FastAPI 백엔드 :8765
- 칼만 fusion 나우캐스팅 (TRIZ #15+#1)
- GradientBoosting 회귀 R²=0.78
- K-means 클러스터링 K=3
- 광고 단가 동적 책정 (가치사슬 3단)
- 비상 동선 추론 (BEV 4분면 + A*)

       ↓

[WS BROADCAST] wss://app.allthatai.kr
┌──────────────────────┬──────────────────────┬──────────────────┐
│ 운영자 콘솔 (4)       │ 시민 PWA              │ 네이티브 (Flutter) │
│ - 3D BEV (Three.js)  │ - 추천 칸             │ - 폰 센서 송신    │
│ - 광고 단가 매트릭스 │ - 분산 인센티브       │ - 임팩트 카운터   │
│ - 비상 동선 시연     │ - citydata 칩         │                  │
└──────────────────────┴──────────────────────┴──────────────────┘
```

### Slide 14 — 사용자 플로우

```
[A] 시민 플로우
앱 실행 → GPS 매칭 → 가까운 역 자동 인식
→ 추천 칸 + ETA → citydata 칩 (날씨/공기)
→ 분산 인센티브 배너 활성 시 -100~200원 안내
→ 탑승 시 [탑승하기] → 임팩트 로깅 (사회적 가치 누적)

[B] 운영자 플로우
콘솔 접속 → 실시간 BEV 3D 점유 시각화
→ 호선/역/시각 슬라이더 조작 → KPI 4종 모니터링
→ 비상 시 [🚨 비상 동선] 클릭 → 4분면 분포 → 최적 출구 자동 추천

[C] 광고주 플로우
광고 단가 페이지 → 12역 × 24시간 인구 밀도 히트맵
→ 역 클릭 시 시간대별 단가 표 (피크/한산)
→ 예상 단가 인상률 + 추가 매출 자동 계산 → 입찰 의사결정

[공통 백본]
동일 백엔드 WebSocket 채널 1개로 운영자·시민·광고주가 같은 데이터 보면서
각자 다른 의사결정. "단일 데이터 파이프라인 → 양면 가치사슬"
TRIZ #5(통합) 적용 사례.
```

---

## 6. 사업화·시장성·발전 가능성 (3장)

### Slide 15 — 정책 ROI

```
| 항목              | 가정                                       | 연간 가치 (보수) |
|-------------------|--------------------------------------------|------------------|
| 통근시간 단축     | 1인 -2분 × 700만명 × 250일 × 1.5만원/시    | 8,750억          |
| 사고 회피         | 압사 등 사회적 비용 1건/년 × 500억         | 500억            |
| 광고 단가 인상    | 지하철 광고 시장 2,000억 × +5%             | 100억            |
| 에너지 효율       | 칸 분산 → 공조 -3% × 4,000억 전력비        | 120억            |
| 합계 (보수)       |                                            | 약 9,470억/년    |

[KPI]
1회성 인프라:    2.55억 (환승허브 85역 × 300만원)
ROI 배수:        3,714× (연간 가치 ÷ 인프라)
투자 회수:       0.1일 (≈ 2.4시간)
낙관 시나리오:   2.68조/년, ROI 5,928×

※ scripts/policy_roi.py 시뮬레이터 — 가정값 변경 시 즉석 재계산. 라이브 시연 가능.
```

### Slide 16 — 사업화 모델 (가치사슬 3단)

```
[1단] 운영자 (B2G)
고객:        서울교통공사, 지자체, 도시철도공사
제품:        칸 단위 점유 분석 + 비상 동선 + 광고 단가 매트릭스 SaaS
가격:        역당 월 30만원 × 환승허브 85역
예상 매출:   3억원/년 (1단계)

[2단] 시민 (B2C)
고객:        서울 일평균 700만 라이드
제품:        무료 PWA + 네이티브 앱 (사용자 데이터가 곧 자산)
가격:        무료 (네트워크 효과 우선)
가치:        데이터 정확도 ↑ → 1단·3단 단가 ↑

[3단] 광고주 (B2B)
고객:        옥외광고 대행사, 자체 광고주
제품:        동적 단가 매트릭스 API + 입찰 시스템
가격:        거래액 5% 수수료
예상 매출:   5억원/년 (단가 +5% × 100억 거래)

[발전 로드맵]
2026 Q3: 서울 환승허브 85역 시범 사업 (B2G)         3억/년
2027:    전국 광역철도 + 광고 매트릭스 베타        15억/년
2028:    버스 BIS 통합 + 시리즈 A 투자 유치        50억/년
2029+:   해외 진출 (도쿄·홍콩·싱가포르)           200억+/년
```

### Slide 17 — 광고 단가 자동화 (1조 시장)

```
[시장 규모]
한국 옥외광고 시장: 1.7조원/년 (2024)
지하철 광고 비중:   ~2,000억원 (옥외광고의 11.8%)
동적 책정 효과:     +5~8% 단가 인상 (+100~160억/년)

[왜 우리만 가능한가 — 진입 장벽]
1. citydata_ppltn 110개 POI 분 단위 인구 데이터 — 서울 한정 가용
2. 역×시간대 매트릭스를 12개 대표 POI 자동 계산 — EDA로 검증된 4 아키타입
3. 분 단위 동적 단가 — 기존 옥외광고는 월 단위 고정가

[광고주 ROI 시나리오]
강남역 18시 — 인구 밀도 95% → 단가 +90%, 노출 가치 +110% → 실질 ROI +20%
한산 13시 — 단가 -40%, 노출 가치 -30% → 실질 ROI +10%
→ 광고주는 두 시간대 모두 이득, 운영자는 +5% 매출 인상. Win-win.
```

---

## 7. 개발 툴 및 참고문헌 (2장)

### Slide 18 — 기술 스택

```
[백엔드]
Python 3.12, FastAPI + WebSockets, Pandas / Scipy / scikit-learn

[컴퓨터비전]
YOLO11s (Ultralytics) — 사람 검출 (CUDA 가속)
BoT-SORT — 다중 객체 추적 (Kalman + ReID)

[프론트엔드]
Three.js + Vanilla JS — 3D BEV 렌더링 (운영자 콘솔)

[네이티브 앱]
Flutter 3.41 + Dart 3.11 — Android APK (Geolocator + WebSocket)

[인프라]
GitHub Pages + Actions — 정적 호스팅 + CI/CD 자동 배포
Cloudflare named tunnel — 영구 도메인 백엔드 외부 노출
cloudflared + 자체 도메인 — app.allthatai.kr (가비아 보유)

[총 비용] 0원 (도메인 갱신비 1.5만원/년 제외). 모든 도구 오픈소스 또는 무료 tier.
[코드]   https://github.com/leelang7/MetroEyes
```

### Slide 19 — 참고문헌 / 데이터 출처

```
[공공 데이터]
- 서울 열린데이터광장 (data.seoul.go.kr): CardSubwayTime, realtimeStationArrival,
  citydata, citydata_ppltn, ListPublicReservationCulture, TimeAverageAirQuality,
  CardSubwayStatsNew, SPOP_DAILYSUM_JACHI
- 공공데이터포털 (data.go.kr): 국토교통부 BIS 버스정류소·노선
- 서울 TOPIS (topis.seoul.go.kr): 도시철도 실시간 도착정보 API

[학술 / 기술 참고]
- Aharon et al. (2022). BoT-SORT: Robust Associations Multi-Pedestrian Tracking. arXiv:2206.14651
- Jocher et al. (2024). YOLO11. Ultralytics
- Altshuller (1984). Creativity as an Exact Science (TRIZ 발명문제 해결 이론). Gordon & Breach
- Welch & Bishop (2006). An Introduction to the Kalman Filter. UNC Chapel Hill TR 95-041
- Hartley & Zisserman (2004). Multiple View Geometry in Computer Vision. Cambridge

[정책·시장 데이터]
- 한국옥외광고센터 (2024). 옥외광고 시장 규모 통계 ─ 1.7조원
- 서울교통공사 (2024). 도시철도 일평균 통행 700만명·전력비 4,000억원/년
- 한국교통연구원 (2023). 통근시간 사회적 비용 분석
```

---

## 마지막 — Slide 20

```
[감사합니다]

데이터의 갱신 주기가 30분이라고,
우리가 본 세상도 30분 평균이어야 할 이유는 없다.

MetroEyes — 자체 CV + TRIZ + 양면 가치사슬
연 1.27조원 사회적 가치, ROI 3,700배

라이브 데모: https://leelang7.github.io/MetroEyes/
백엔드:      wss://app.allthatai.kr
코드:        https://github.com/leelang7/MetroEyes
```

---

## 작성 가이드 / 제출 체크리스트

- [ ] 한쇼/PPT 페이지 분량 **10~30페이지 내외** (현재 21장)
- [ ] **개인정보 기재 금지** (표지에만 성명 "이상철")
- [ ] PPT 디자인·폰트 자유. 폰트 사용 시 **[파일에 글꼴 포함]** 으로 저장
- [ ] 활용 공공데이터 목록을 본 슬라이드 5(Slide 5)에 정확하게 기재 — 형식: `서울 열린데이터광장 - 데이터셋명`
- [ ] 파일명: **이상철_MetroEyes_상세기획서.pdf** (또는 .ppt)
- [ ] 참가신청서/사회조사서/개인정보 동의서는 별도 PDF 제출
- [ ] 로고 이미지 별도: `assets/metroeyes_logo.svg` 또는 PNG
- [ ] 화면 이미지: `outputs/demo/operator_realbev.png` 등 활용
