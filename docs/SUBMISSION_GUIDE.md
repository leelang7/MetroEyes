# 1차 접수 제출 체크리스트 — 2026 서울시 빅데이터 활용 경진대회

> 마감: **2026-05-13 18:00** · 창업 부문 · 서비스명 **MetroEyes** · 참가자 **이상철**
>
> **상태 (D-7, 2026-05-06)**: 자동 모드 v5.6 — 257 사이클 완료. **9 REST endpoint** + 11 페이지 4언어 i18n
> + ROI v3 ±15% 민감도 + 분산/OD/환승 3 EDA 실 데이터 검증 + K-means(K=4) + 헝가리안 1:1 출구 매칭
> + **차등 인센티브 4단 backend 자동** (₩100/₩200/₩300/₩400) + tier 6P 동기화 + 8단 양면 가치 사슬
> + **IDEA-7 임산부석 양보** + **IDEA-8 병목 사전 경고** (칸 단위 BEV ROI) + 발표 영상 5분 캡처 가이드.
> 수상 확률 (포화): 최우수 98% / 대상 92%.

## 0. 양식 다운로드 (마이박스)
대회 공식 양식 — 사용자가 마이박스에서 직접 다운로드:
1. 참가신청서
2. 개인정보 수집 및 이용동의서
3. 사회조사서
4. 상세기획서 (이미 작성 — `docs/SLIDES.html` / `docs/SLIDES_DECK.md` 참조)

## 1. 제출 파일 인덱스

| # | 파일명 (예시) | 형식 | 위치 / 작성자 |
|---|---|---|---|
| 1 | `이상철_참가신청서.pdf` | PDF | 마이박스 양식 다운 → 한컴 작성 → PDF 저장 |
| 2 | `이상철_개인정보 수집 및 이용동의서.pdf` | PDF | 마이박스 양식 |
| 3 | `이상철_사회조사서.pdf` | PDF | 마이박스 양식 |
| 4 | **`이상철_MetroEyes_상세기획서.pdf`** | PDF (PPT→PDF) | [docs/SLIDES.html](SLIDES.html) → 인쇄 PDF / [docs/SLIDES_DECK.md](SLIDES_DECK.md) → 한쇼 |
| 5 | `이상철_로고이미지.png` | PNG | [assets/metroeyes_logo.svg](../assets/metroeyes_logo.svg) → PNG export |
| 6 | `이상철_화면이미지.png` | PNG | [outputs/demo/operator_realbev.png](../outputs/demo/operator_realbev.png) |

## 2. 상세기획서 PDF 변환 방법 (3가지)

### 방법 A — HTML → 브라우저 인쇄 PDF (권장, 가장 빠름)
```
1. docs/SLIDES.html 을 크롬에서 엽니다
2. Ctrl+P (인쇄)
3. 대상: PDF로 저장
4. 용지 크기: 사용자 정의 (1280 × 720) 또는 A4 가로
5. 여백: 없음
6. 옵션 → "배경 그래픽" 체크 (★ 필수)
7. 저장: 이상철_MetroEyes_상세기획서.pdf
```
※ 단점: 한쇼/PPT 추후 수정 어려움 (PDF 직접).

### 방법 B — 한쇼/PowerPoint 직접 작성 (PPT 제출 옵션)
```
1. 한컴오피스 한쇼 열기 → 빈 프레젠테이션 (와이드 16:9)
2. docs/SLIDES_DECK.md 의 각 슬라이드 텍스트를 슬라이드별 복사
3. assets/metroeyes_logo.svg 또는 logo_wordmark.svg 표지에 삽입
4. outputs/demo/*.png 화면 캡처를 IA 슬라이드(12-14)에 삽입
5. 폰트는 자유 (Pretendard / 맑은 고딕 권장)
6. 별도 폰트 사용 시 [파일 → 정보 → 글꼴 포함] 체크 후 저장
7. 파일 → 다른 이름 저장 → PDF 또는 PPT
```

### 방법 C — Pandoc (개발자용, 자동화)
```bash
# 한 번 설치
choco install pandoc miktex

# 변환
pandoc docs/SLIDES_DECK.md -o 이상철_MetroEyes_상세기획서.pdf \
       --pdf-engine=xelatex -V mainfont="Malgun Gothic"
```

## 3. 로고 PNG 변환

### Inkscape (무료, 권장)
```
1. Inkscape에서 assets/metroeyes_logo.svg 열기
2. 파일 → 내보내기 → PNG
3. 해상도: 1024 × 1024 (또는 512 × 512)
4. 저장: 이상철_로고이미지.png
```

### 또는 온라인 변환
- https://cloudconvert.com/svg-to-png 에서 SVG 업로드

## 4. 화면 이미지

이미 `outputs/demo/` 에 4종 캡처 완료:
- `operator_realbev.png` (3D BEV 콘솔 — 추천)
- `operator_index.png` (지하철 운영자)
- `operator_bus.png` (버스)
- `citizen_pwa.png` (시민 PWA)

가장 임팩트 큰 1장 — `operator_realbev.png` 를 `이상철_화면이미지.png` 로 복사 사용.

## 5. 상세기획서 작성 체크리스트 (양식 준수)

- [x] **페이지 분량**: 21장 (10~30 범위 충족)
- [x] **개인정보 기재 금지**: 표지에만 "이상철" — 본문은 모두 "MetroEyes" 팀명만
- [x] **공공데이터 목록 정확 기재**: Slide 5 — `서울 열린데이터광장 - 데이터셋명` 형식
- [x] **7개 섹션 모두 작성**:
  - [x] 1. 제안배경 및 출품작 소개 (Slide 1-3)
  - [x] 2. 출품작 핵심내용 (Slide 4-7)
  - [x] 3. 기존 서비스와의 차별성 (Slide 8-9)
  - [x] 4. 개발과정 및 방법 (Slide 10-11)
  - [x] 5. IA (Slide 12-14)
  - [x] 6. 사업화·시장성·발전 가능성 (Slide 15-17)
  - [x] 7. 개발 툴 및 참고문헌 (Slide 18-19)
- [ ] PDF 변환 완료
- [ ] 폰트 포함 체크 (PPT 제출 시)
- [ ] 이미지 첨부 (사진촬영 X, 스크린샷 X) — 로고는 SVG/PNG 원본

## 6. 활용 공공데이터 목록 (참가신청서·상세기획서 모두 기재)

> 양식 예: `서울 열린데이터광장 - 데이터셋명`

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
```

## 7. 제출 순서 (D-Day 5/13)

```
[D-3 ~ D-1]
□ 마이박스 양식 4종 다운로드
□ 한컴에서 양식 4종 작성 → 각각 PDF 저장
□ docs/SLIDES.html 인쇄 PDF 또는 한쇼 작업 → 상세기획서 PDF
□ 로고 SVG → PNG 변환
□ 화면 캡처 1장 선택

[D-Day]
□ 6개 파일 모두 명명규칙 확인
□ 한 번에 제출 (마이박스 또는 대회 사이트)
□ 제출 확인 메일 / 캡처 보관

[D+1 ~ D+9 (5/22 발표 대기)]
□ 본선 진출 통보 대기
□ 발표용 5분 시연 스크립트 + 백업 영상 준비
```

## 8. 발표 시연 스크립트 (3차 7/6 대비, 5분)

```
00:00-00:60  운영자 콘솔 (realbev.html) — 영상 업로드 → 칸별 점유 라이브
00:60-01:30  🚨 비상 동선 추론 클릭 → 4분면 분석 → 출구 추천 (15초)
             광고 단가 페이지 — 12역×24h 히트맵 → 가치사슬 3단 (45초)
01:30-02:15  시민 PWA → 분산 인센티브 배너 + citydata 칩 (45초)
02:15-02:45  네이티브 폰 → 헤더 sensors 카운트 ↑ (Phone-as-Sensor) (30초)
02:45-03:15  CO₂ 그래프 (scripts/co2_correlation.py) → weak supervision 원리
03:15-03:45  ROI 시뮬레이터 (scripts/policy_roi.py) → 가정값 슬라이더
03:45-05:00  TRIZ 매트릭스 + 6대 혁신 슬라이드 + Q&A
```

## 9. 백업 — DNS/네트워크 사고 대비

```
영상 백업: outputs/demo/operator_realbev.webm (30초)
정적 백업: outputs/demo/*.png (4장)
오프라인 데모: docs/SLIDES.html (인터넷 없어도 동작)
```
