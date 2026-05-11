# 2차 발표 Q&A 준비 — 예상 어려운 질문 + 데이터 근거 답변 (cycle 378)

> 본선 평가 (2026-07-06) 발표 후 심사위원 Q&A 5~10분 대비.
> 모든 답변은 **30초 이내** + **수치 근거** + **CI 검증 가드 ID** 형식.

---

## 🔥 카테고리 1 — 통계 / 정량 검증

### Q1. "응답률 30% 가정의 근거는?"
**근거 (15초)**: Singapore GP-S 시범 (2018) 5% × MetroEyes 차등 보상 4단 효과 6배 = 30%. 보수적 중간값.
**증거**: `scripts/policy_roi_v3.py` 5 시나리오 (5/15/30/50/70%) — 응답률 슬라이더 라이브 시뮬 가능.
**보강**: Monte Carlo 1,000회 95% CI [1,064~1,808억] — 30% 가정 변동 ±15% 하에서도 1,393억은 안전.

### Q2. "Monte Carlo perturbation 4축은 어떻게 정했나?"
**근거 (20초)**: 실제 정책 채택률 변동성 데이터 기반 — (1) 응답률 ±15% (정책 채택률 표준 변동), (2) 통근 절감분 ±20% (역별 분포), (3) 시간가치 ±10% (한국교통연구원 167원/분 변동), (4) 호선 cap ±10% (운영 변동).
**증거**: `frontend/figs/policy_roi_v3_ci_band.json` · seed=42 재현 가능 · `tests/test_roi_ci_band.py` 7 가드.

### Q3. "광고된 1,393억과 정확히 어떻게 일치하나?"
**근거 (10초)**: Canonical KPI JSON (`policy_roi_v3_canonical_kpi.json`) 가 진실의 원천. CI 매 push 마다 pitch / onepager / SLIDES / PROPOSAL 동시 일치 자동 검증.
**증거**: `tests/test_kpi_drift.py` 6 가드 (cycle 375) — 광고-코드 충돌 자동 차단.

### Q4. "EDA 결과 σ −9% 가 시뮬이 아니라 실제인 건가?"
**근거 (20초)**: CardSubwayTime 202602 (서울 열린데이터광장 공식) 28일 평균 1~9 호선 실 데이터로 검증. 시뮬 아닌 *실제 평탄화*. σ 129,618 → 117,940.
**증거**: `frontend/figs/dispersion_sim_report.json` · `tests/test_eda_dispersion.py` 6 가드.

---

## 🔧 카테고리 2 — 기술 / 구현 가능성

### Q5. "BEV CV 가 정말 1280p 에서 5Hz 동작?"
**근거 (15초)**: YOLO11n + BoT-SORT, RTX 4070 SUPER 에서 측정. Jetson Orin (24 TOPS) 기준 INT8 quant 시 4-7 Hz 보장.
**증거**: `src/cv/tesla_bev.py` `--imgsz 1280` 기본값 · `--demo` 모드 fake BEV broadcast 시연.

### Q6. "REST API 10 endpoint 가 정말 production 수준?"
**근거 (15초)**: OpenAPI 3.0 spec (`/api/openapi.yaml`) Swagger/Redoc/Postman 자동 import 가능. CORS 활성화 + JSON 표준 응답.
**증거**: `tests/test_openapi_spec.py` 4 가드 — 10 endpoint enum + IDEA-7/8 incident type + breakdown 자동 검증.

### Q7. "장애 시 시연 끊기지 않나?"
**근거 (10초)**: 8 단 fail-safe — `--demo` (CV 없이도 OK) + 30초 incident injector + 5분 sticky bar + warm seed 12건 + Docker compose + GitHub Actions CI + KPI drift 자동 차단 + RUNBOOK 9 시나리오.
**증거**: `docs/RUNBOOK.md` (cycle 376) · `tests/test_runbook.py` 7 가드.

### Q8. "Claude Haiku LLM 의존성 — API 죽으면?"
**근거 (10초)**: Naver 뉴스 자동 fallback (60자 title) → broadcast 정상 + 30분 캐시 (localStorage) → 직전 컨텍스트 유지.
**증거**: `src/cv/tesla_bev.py` `fetch_context_news()` try/except + `frontend/operator_web/ad_pricing.html` AD_LLM_KEY localStorage.

---

## 💼 카테고리 3 — 사업화 / 시장성

### Q9. "Y3 ₩200억 매출 — 어떻게 달성?"
**근거 (25초)**: 3-tier BM. (1) B2G SaaS ₩40억 — 서울 + 5 광역시 ₩3-8억/도시. (2) B2B 광고 API rev share ₩100억 — ₩2,000억 시장의 5% × 4-7%. (3) B2B Data API ₩12억 — 50 광고주 × ₩2,400만/년.
**증거**: `docs/PROPOSAL.md` §11 + `frontend/onepager.html` 사업화 3-tier 카드.

### Q10. "시민 인센티브 ₩100~₩400 자금은 누가 부담?"
**근거 (15초)**: **운영자 (서울교통공사)** 비용 — 회사 수익과 분리. ROI 347x 이므로 도시철도 운영비 절감 근거 제공 → 정책 통과 동기.
**증거**: `docs/PROPOSAL.md` §11.3 자금 흐름 표 + 정책 v3 분리 모델.

### Q11. "London / Tokyo / Singapore 가 이미 있는데 차별점?"
**근거 (20초)**: 모두 *역 단위 통계*. MetroEyes 는 *칸 단위 BEV* + *분산률 차등 보상* + *backend 누적 라이브 ROI*. 3 축 통합. Singapore GP-S 응답률 ~5% vs MetroEyes 30% (차등 보상 6배 효과).
**증거**: `docs/PROPOSAL.md` §13 4 도시 비교 표 · `frontend/onepager.html` (4 도시 표).

### Q12. "Y1 매출 0 인데 어떻게 운영?"
**근거 (15초)**: PoC 단계 — 서울교통공사 2026 Q4 시범 도입 협약. 정부 지원 (창업 부문 상금 + 서울시 빅데이터 활용 사업 후속) + Series A ₩50억 (2027 Q3) 로 18개월 runway. K-startup 청년창업 1,000 + TIPS 5억 매핑.
**증거**: `docs/PROPOSAL.md` §14 3년 로드맵 표.

---

## ♿ 카테고리 4 — 윤리 / 법 / 사회

### Q13. "BEV CV 가 개인정보 침해 아닌가?"
**근거 (15초)**: **Edge AI** — 영상 frame 은 Jetson Orin 안에서만 처리. broadcast 는 익명 BEV 트랙 (x,y,bbox,id) 만. **개인정보 zero**, 얼굴/번호판 어디에도 저장 안 됨.
**증거**: `docs/PROPOSAL.md` §3 Edge AI + `frontend/admin.html` ESG 패널 "🛡 개인정보 노출 zero" 라이브 표시.

### Q14. "차등 보상이 약자 차별 아닌가?"
**근거 (20초)**: 반대 — *분산 행동 자체* 에 보상이라 경제 약자 우대. 더 핵심: IDEA-9 5중 모달리티 도착 알림으로 청각 약자 42만명 + 노이즈 캔슬링 1,200만명 잠재 보호.
**증거**: `frontend/passenger_app/index.html` IDEA-9 + `frontend/admin.html` ESG "♿ 약자 수혜" 라이브 카운터.

### Q15. "탄소중립 기여도?"
**근거 (15초)**: 분산 1회 = 자가용 회피 5% × 평균 통근 8.4km × 0.21 kg CO₂/km = **0.012 kg eq**. 700만 × 30% × 0.45 = 945,000 분산 행동/일 × 0.012 = **11.3 톤 CO₂/일**.
**증거**: `frontend/admin.html` ESG "🌱 CO₂ 절감" 라이브 카운터 (impact_summary broadcast 직결).

### Q15-A. "시민 신고가 지하 터널에서 끊기면?"
**근거 (15초)**: **오프라인 큐 구현 완료** — `localStorage['metroeyes_report_queue']` 에 최대 10건 보관 → WebSocket 재연결 시 `flushReportQueue()` 자동 전송. 30초 쿨다운으로 스팸 방지.
**증거**: `tests/test_citizen_report_pwa.py::test_offline_queue_localStorage` 가드.

### Q16. "데이터 의존성 — 서울 외 도시는?"
**근거 (15초)**: 서울 열린데이터광장 7 API + 공공데이터포털 + 자체 CV 백엔드. 부산/대구/인천도 동일 구조 (지자체 OpenAPI 표준화). Y3 8 광역시 확장 로드맵.
**증거**: `README.md` 10 API 표 + `docs/PROPOSAL.md` §14 인력 plan.

---

## 🎯 카테고리 5 — 발표 흐름 / 전략

### Q17. "5분 시연이 너무 빠른데 모든 기능을 어떻게 다 보여주나?"
**근거 (15초)**: `frontend/demo.html` 4-패널 동시 + 자동 SCRIPT (cycle 363). 14 stage timestamp 정합 + AI 단가 / A* 강화 / 호선 ROI overlay 자동 표시.
**증거**: `tests/test_demo_orchestration.py` 5 가드 + `docs/RECORDING_NARRATION.md` 4 언어 narration 14 stage × 4 = 56 블록.

### Q18. "수상 후 다음 단계?"
**근거 (15초)**: 2026 Q4 서울교통공사 PoC → 2027 H1 부산·대구·인천 확장 → 2027 H2 Series A ₩50억 → 2028 Y2 ₩100억 매출 → 2029 Y3 ₩200억 + 사회 가치 1,393억/년 정량.
**증거**: `docs/PROPOSAL.md` §14 3년 로드맵.

---

## 📊 답변 시 필수 cross-reference

| 질문 종류 | 첫 응답 키워드 | 즉시 보일 화면 |
|---|---|---|
| 통계 신뢰도 | "Monte Carlo 1,000회 CI [1,064~1,808억]" | `pitch.html` § Monte Carlo callout |
| 호선별 정책 답 | "2호선 ROI 708x · 157M분" | `admin.html` 라이브 추천 패널 |
| 운영 안정성 | "8단 fail-safe + RUNBOOK 9 시나리오" | `docs/RUNBOOK.md` 표 |
| AI 혁신성 | "AI 4축 + Claude Haiku 라이브 컨텍스트" | `admin.html` AI 패널 |
| 사업화 | "B2G/B2B 3-tier Y3 ₩200억" | `onepager.html` 사업화 카드 |
| 약자 보호 | "IDEA-9 5중 모달리티 + ESG 5축" | `admin.html` ESG 라이브 |
| 시민 참여 | "시민 신고 FAB 3종 + 오프라인 큐 + 자동 전송" | `passenger_app/index.html` 신고 버튼 |

---

## 🛡 답변 회피해야 할 표현

❌ **"잘 모르겠습니다"** — 대신: "현재 데이터 기반으로는 X. 추가 검증 필요시 Y 방법으로."
❌ **"아직 구현 안 됐습니다"** — 대신: "현재는 데모 모드로 시연. 운영 단계는 Y3 로드맵에서 X."
❌ **"비슷한 게 있긴 한데..."** — 대신: "London / Tokyo / Singapore 모두 *역 단위*. MetroEyes 는 *칸 단위 BEV*."

---

## 30초 self-pitch (모든 질문 끝에 가능)

> "MetroEyes 는 자체 CV BEV + 10 공공 API + 시민 인센티브 3 축 통합 시스템입니다.
> 정책 ROI v3 + Monte Carlo 1,000회 검증으로 사회 가치 1,393억/년 [CI 1,064~1,808] 정량 도출.
> 2호선 ROI 708x — 정책 결정 즉답. 8단 fail-safe + 341 회귀 가드 + 4 언어 i18n 으로 production-grade 신뢰성 확보했습니다."
