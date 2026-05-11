# 마이박스 양식 4종 — 사전 작성 데이터 (cycle 401)

> D-day (5/13) 직전 한컴 양식에 copy-paste 즉시 활용 가능한 데이터 모음.
> 양식: 1) 참가신청서 2) 개인정보 동의서 3) 사회조사서 4) 상세기획서

---

## 1. 참가신청서 (이석창_참가신청서.pdf)

### 기본 정보
- **참가자 성명**: 이석창
- **이메일**: leescvsir@gmail.com
- **참가 부문**: 창업 부문
- **출품작 명**: MetroEyes (코드명: SubwayBEV)
- **한 줄 요약**: 자체 CV BEV + 10 공공 API + 시민 분산 인센티브 — 3축 통합 시스템으로 도시 교통 평탄화

### 활용 공공데이터 (양식 형식: `서울 열린데이터광장 - 데이터셋명`)
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
공공데이터포털 - IndoorAirQualityMeasureService (지하역사 실내 공기질)
공공데이터포털 - SubwayElevatorStatus (서울 지하철 엘리베이터 운행 현황)
```

### 핵심 KPI (canonical, cycle 374 이후 정확)
- **사회적 가치**: 1,393억원/년 (Monte Carlo 95% CI [1,064~1,808억])
- **ROI**: 347x (CI [270~424x])
- **절감 시간**: 473.4M분/년
- **2호선 단독**: 157M분 (33%) · ROI 708x

### 기술 스택
- **CV**: YOLO11n + BoT-SORT + 호모그래피 BEV (Edge AI Jetson Orin)
- **Backend**: Python WebSocket + REST API v1 (13 endpoint, OpenAPI 3.0)
- **Frontend**: 11 페이지 4언어 (ko/en/zh/ja) PWA + 운영자 콘솔
- **AI**: Claude Haiku 4.5 (LLM 자동 컨텍스트) + GBR R²=0.931 + Web Speech STT

---

## 2. 개인정보 수집 및 이용동의서

표준 동의서 — 마이박스 양식 그대로 다운로드 → 서명 후 PDF 저장.

체크 사항:
- [x] 개인정보 수집·이용 동의
- [x] 개인정보 제3자 제공 동의 (필요시)
- [x] 마케팅 활용 동의 (선택)

---

## 3. 사회조사서

### 출품작이 해결하는 사회 문제
> 서울 도시철도 일평균 700만 통행자가 8시·18시 양봉 피크에 만석 칸 (cap 110~150%) 집중.
> 평균 점유율은 정상이나 *칸 단위 분포*가 보이지 않아 안전·통근시간·에너지 손실 발생.
> 공공 데이터는 30분 평균 통계만 — 칸 단위 실시간 분산 정책 불가능.

### 사회적 가치
1. **통근시간 단축**: 473.4M분/년 → 1,183억 (한국교통연구원 167원/분)
2. **사고 회피**: 만석 호선 압사 위험 ↓ → 348억
3. **광고 시장 활성**: 2,000억 시장 +5% → 85억
4. **에너지 효율**: 4,000억 전력비 −3% → 58억
5. **인센티브 비용**: 700만 × 30% × 0.45 × ₩100 = −282억
- **순 사회적 가치**: 1,393억원/년 (Monte Carlo 95% CI [1,064~1,808억])

### ESG 5축
- **🌱 ENV**: CO₂ 절감 — ultra (광고 보수): 2,834 톤/년 / standard (실효): 20,837 톤/년 (한국인 1,736년 배출 등가)
- **♿ SOC**: 청각 약자 42만 + 노이즈 캔슬링 1,200만 잠재 사용자 (IDEA-9 5중 모달리티)
- **💼 JOB**: Y3 신규 25 FTE 고용
- **🤝 CO**: 8단 양면 가치 사슬 (시민 ↔ 운영자 ↔ 광고)
- **🛡 GOV**: 개인정보 zero (Edge AI on-device, 익명 BEV 트랙만 broadcast)

### 기존 솔루션 차별성
| 도시 | 정책 | 단위 |
|---|---|---|
| 🇬🇧 London | Off-Peak 30% 할인 | 역 단위 RFID |
| 🇯🇵 Tokyo | Suica 월 정액 | 통근 구간 통계 |
| 🇸🇬 Singapore | GP-S 25¢ (2018) | EZ-Link 카드 |
| 🇰🇷 **MetroEyes** | **분산률 차등** (5%p +₩100, 30%p +₩200) | **자체 CV BEV (cap 30~150%)** |

---

## 4. 상세기획서 (이석창_MetroEyes_상세기획서.pdf)

### 변환 방법 — 3가지 (`docs/SUBMISSION_GUIDE.md` §2 참조)

**방법 A — HTML → 브라우저 인쇄 PDF (권장)**:
1. `docs/SLIDES.html` 크롬 열기 → Ctrl+P → PDF 저장
2. 용지 1280×720 사용자 정의 + 여백 없음 + 배경 그래픽 ✓
3. 파일명: `이석창_MetroEyes_상세기획서.pdf`

**방법 B — 한쇼/PowerPoint 직접**:
1. `docs/SLIDES_DECK.md` 텍스트 → 한쇼 빈 16:9 슬라이드 복사
2. `assets/metroeyes_logo.svg` 표지 + `outputs/demo/*.png` IA 슬라이드
3. PDF 또는 PPT 저장 (폰트 포함)

**방법 C — Pandoc**:
```bash
pandoc docs/SLIDES_DECK.md -o 이석창_MetroEyes_상세기획서.pdf \
       --pdf-engine=xelatex -V mainfont="Malgun Gothic"
```

### 7개 섹션 (양식 준수, 21장)
- 1. 제안배경 + 출품작 소개 (Slide 1-3)
- 2. 출품작 핵심내용 (Slide 4-7) — 3축 통합, ROI v3, IDEA 9
- 3. 기존 서비스와의 차별성 (Slide 8-9) — 4 도시 비교
- 4. 개발과정 + 방법 (Slide 10-11) — TRIZ 8 모순 + 6 IDEA
- 5. IA (Slide 12-14) — 운영자 / 시민 / 광고 화면 캡처
- 6. 사업화·시장성·발전 가능성 (Slide 15-17) — Y3 ₩200억 BM
- 7. 개발 툴 + 참고문헌 (Slide 18-19)

### 페이지별 핵심 메시지

**Slide 1 (한 줄 요약)**:
> 자체 CV·10개 공공 API·5대 도전 해법으로 "칸별 점유"와 "안내 단절"이라는 빈 칸을 채우고,
> 운영자·시민·광고주 3단 가치사슬로 **연 1,393억 [Monte Carlo 95% CI 1,064~1,808억] 사회적 가치** 정량화.

**Slide 19 (정책 ROI v3)**:
> Monte Carlo 1,000회 4축 perturbation × 5 시나리오 → 30% 시나리오 1,393억 [1,064~1,808] · ROI 347x [270~424].
> 호선별 1순위 = 2호선 ROI 708x · 138M분 절감 · 사회 가치 315억.

---

## 5. 화면 캡처 (이석창_화면이미지.png)

`outputs/demo/operator_realbev.png` 가 가장 임팩트 큼 (3D BEV 콘솔 + 실 카메라).

대안:
- `outputs/demo/citizen_pwa.png` — 시민 PWA (4언어 + IDEA-9)
- `outputs/demo/operator_index.png` — 지하철 운영자 콘솔

---

## 6. 로고 (이석창_로고이미지.png)

- 원본: `assets/metroeyes_logo.svg`
- 변환: Inkscape 또는 cloudconvert.com (1024×1024 권장)

---

## 7. 제출 체크리스트 (D-Day 2026-05-13 18:00)

```
[D-3 ~ D-1]
□ 마이박스 양식 4종 다운로드
□ 한컴에서 양식 4종 작성 → 각각 PDF 저장
□ docs/SLIDES.html 인쇄 PDF → 상세기획서 PDF
□ 로고 SVG → PNG 변환
□ 화면 캡처 1장 선택

[D-Day 5/13 18:00]
□ 6개 파일 모두 명명규칙 확인 (이석창_X.pdf/png)
□ python scripts/submission_check.py — 12 항목 PASS 확인
□ python -m pytest tests/ -q — 337+ tests passed 확인
□ 한 번에 제출 (마이박스 또는 대회 사이트)
□ 제출 확인 메일 / 캡처 보관

[D+9 (5/22 본선 진출 통보 대기)]
□ 본선 발표용 5분 시연 + 4언어 narration 준비
□ docs/QA_PREPARATION.md 18 예상 질문 답변 reherse
```

---

## 8. 한 줄 자기 소개 (모든 양식 공통)

> "MetroEyes는 자체 CV BEV + 10 공공 API + 시민 분산 인센티브 3축 통합 시스템으로,
> Monte Carlo 1,000회 95% CI 통계 검증 사회 가치 1,393억/년 (CI 1,064~1,808억) 정량 도출.
> 2호선 ROI 708x — 정책 결정 즉답. 8단 fail-safe + 389 회귀 가드 + 4언어 i18n production-grade."

(글자수: 한국어 132자 / 영어 약 250자)
