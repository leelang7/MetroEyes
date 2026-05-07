# Contributing to MetroEyes

> 2026 서울시 빅데이터 활용 경진대회 (창업 부문) 출품작
> 메인 라인 = D-5 마감 + 본선 7/6 일정 — 안정성 우선.

## 빠른 시작

```powershell
# 1. clone + 설치
git clone https://github.com/leelang7/MetroEyes.git
cd MetroEyes
pip install -e .

# 2. 시연 (CV 모델 없이도 OK)
python -m src.cv.lite_server --port 8765 --demo

# 3. 회귀 검증
python -m pytest tests/ --ignore=tests/test_smoke.py -q
# 기대: 186+ passed

# 4. 제출 직전 자가 검증
python scripts/submission_check.py --ci
# 기대: 10/10 PASS (1초 내)
```

## 작업 흐름

1. **Issue 등록** — [bug_report](.github/ISSUE_TEMPLATE/bug_report.md) / [feature_request](.github/ISSUE_TEMPLATE/feature_request.md)
2. **branch 생성** — `feat/cycle-XXX-short-name` / `fix/cycle-XXX-bug`
3. **개발** — 회귀 가드 먼저 + 구현 + 가드 PASS 확인
4. **PR** — [PULL_REQUEST_TEMPLATE](.github/PULL_REQUEST_TEMPLATE.md) 모든 체크박스 ✓
5. **CI PASS 후 merge** — main 진입 = "submission-ready" 보장 (cycle 380 ship-gate)

## 핵심 룰

### 광고 KPI 변경 시 (cycle 374 회귀 방지)

광고 자료 (`README` / `pitch.html` / `onepager.html` / `SLIDES.html` / `PROPOSAL.md`) 의 수치는
**`frontend/figs/policy_roi_v3_canonical_kpi.json` 가 진실의 원천**.

| 작업 | 명령 |
|---|---|
| canonical KPI 갱신 | `python scripts/policy_roi_v3.py` |
| 광고 자료 동시 일치 | 5+ 광고 자료 수동 동기화 |
| 정합 검증 | `python -m pytest tests/test_kpi_drift.py` (6 가드) |

### 새 기능 추가 시

회귀 가드 3+ 함께 작성:
- DOM / 함수 정의 존재
- 핵심 동작 / 임계값
- 의존 파일 (JSON / 다른 페이지) 존재

예시: cycle 358 A* 강화 → `tests/test_evac_strengthen.py` 5 가드.

### 문서 변경 시

CHANGELOG 5+ cycle 누적 시 v6.X+1 블록 추가:
```bash
python -m pytest tests/test_changelog_freshness.py  # CHANGELOG drift 자동 감지
```

## 참고 자료

- [📕 docs/RUNBOOK.md](docs/RUNBOOK.md) — 장애 9 시나리오 1줄 복구
- [💬 docs/QA_PREPARATION.md](docs/QA_PREPARATION.md) — 18 예상 질문
- [🎯 docs/SUBMISSION_INDEX.md](docs/SUBMISSION_INDEX.md) — 평가 지표 ↔ 산출물 매핑
- [📖 docs/PROPOSAL.md](docs/PROPOSAL.md) — 상세 기획서

## 라이선스

Apache 2.0 — 자유롭게 fork / 학습 / 수정 / 재배포.

## 연락

- 개발: 이상철 · leescvsir@gmail.com
- Issues: https://github.com/leelang7/MetroEyes/issues
