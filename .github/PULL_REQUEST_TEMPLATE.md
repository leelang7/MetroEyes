<!--
MetroEyes PR template — cycle 385
체크: 회귀 가드 모두 PASS / canonical KPI 불일치 없음 / RUNBOOK 영향 없음
-->

## 무엇 / 왜
<!-- 1~2 줄로 — "이 PR이 어떤 사이클의 어떤 작업인지" -->

cycle ___:

## 변경 영향 카테고리

- [ ] 코드 (CV / API / frontend)
- [ ] 광고 자료 (README / pitch / onepager / SLIDES / PROPOSAL)
- [ ] EDA / 모델 (scripts/eda_* / policy_roi*)
- [ ] 문서 (RUNBOOK / QA / CHANGELOG)
- [ ] CI / 테스트 (.github/workflows / tests/)

## KPI 영향

- [ ] 광고 KPI 수치 변경 없음
- [ ] 광고 KPI 변경 시 — `frontend/figs/policy_roi_v3_canonical_kpi.json` 갱신 + 5+ 광고 자료 동시 동기화 (cycle 374 회귀 회피)

## 회귀 가드

- [ ] `python -m pytest tests/ --ignore=tests/test_smoke.py -q` PASS
- [ ] `python scripts/submission_check.py --ci` PASS (CI ship-gate)
- [ ] CHANGELOG 업데이트 (cycle 5+ 누적 시)
- [ ] README 배지 업데이트 (cycle / 가드 수)

## 체크리스트

- [ ] `python -m pytest tests/test_kpi_drift.py` PASS — canonical KPI 동시 일치
- [ ] 4언어 영향 시 — `tests/test_i18n_admin_ad.py` PASS
- [ ] 새 기능 추가 시 — 회귀 가드 추가 (3+ 가드 권장)

## 시연 / 검증

<!-- backend / frontend 변경 시 시연 절차 (포트, URL, 클릭 순서) -->

cf. [`docs/RUNBOOK.md`](docs/RUNBOOK.md) — 장애 시 1줄 복구
