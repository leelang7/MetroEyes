# Security Policy — MetroEyes

> 2026 서울시 빅데이터 활용 경진대회 출품작 · Apache 2.0 · cycle 386

## 개인정보 보호 (Privacy by Design)

MetroEyes는 **Edge AI** 아키텍처로 개인정보 노출을 0 으로 설계:

| 항목 | 처리 위치 | 외부 전송 |
|---|---|---|
| 영상 frame | Jetson Orin (Edge) **on-device only** | ❌ 전송 안 함 |
| 얼굴 / 번호판 | 어디에도 저장 / 전송 안 됨 | ❌ |
| BEV 트랙 (id, x, y, bbox) | broadcast | ✅ 익명 좌표만 |
| 시민 GPS (PWA) | 폰 안 매칭 후 station 이름만 | ✅ 역명만 |

**근거**: `src/cv/tesla_bev.py` track payload 검증 + `frontend/admin.html` ESG 패널
"🛡 개인정보 노출 zero (Edge AI)" 라이브 표시.

## 취약점 보고

보안 취약점 발견 시 — **공개 GitHub Issue 대신 직접 이메일**:

📧 **leescvsir@gmail.com**

48시간 내 응답 + 7일 내 패치 목표.

## 의존성 보안

| 라이브러리 | 라이선스 | 신뢰도 |
|---|---|---|
| YOLO11n + Ultralytics | AGPL-3.0 | 공식 GitHub release pinned |
| BoT-SORT | MIT | 공식 GitHub release pinned |
| websockets (Python) | BSD | PyPI 공식 release pinned |
| Three.js | MIT | CDN with SRI hash |
| Anthropic Claude API | commercial | TLS 1.3 + API key env var |
| Naver Search API | commercial | TLS 1.3 + API key env var |
| Seoul OpenAPI | CC-BY | 공공 데이터 공식 endpoint |

## API 키 / 시크릿 관리

| Secret | 저장 위치 | 노출 방지 |
|---|---|---|
| ANTHROPIC_API_KEY | `.env` (gitignored) | ✅ git 추적 안 함 |
| NAVER_CLIENT_ID/SECRET | `.env` (gitignored) | ✅ |
| 서울 OpenAPI 키 | `.env` (gitignored) | ✅ |
| Cloudflare 터널 cert | `~/.cloudflared/` | ✅ user home 외부 |

`.env` 파일 git 추적 차단 — `.gitignore` 검증 가드: `tests/test_smoke.py` (개발 안전장치).

## 자동 보안 검증

| 검증 | 명령 | 빈도 |
|---|---|---|
| 의존성 취약점 (pip-audit) | `pip-audit` | 권장 (월간) |
| 시크릿 누출 (gitleaks) | `gitleaks detect` | PR 시 |
| 광고 KPI ↔ 코드 정합 | `pytest tests/test_kpi_drift.py` | 매 push |
| 12 항목 ship-gate | `python scripts/submission_check.py --ci` | 매 push |

## 보안 사고 연락

- 취약점 발견: **leescvsir@gmail.com** (1순위)
- 일반 버그: [GitHub Issues](https://github.com/leelang7/MetroEyes/issues) (`bug_report.md` 양식)
- 운영 장애: [`docs/RUNBOOK.md`](docs/RUNBOOK.md) 9 시나리오 1줄 복구

---

📅 **본선 평가 (2026-07-06) 직전 1시간**: 새 commit 금지 — 회귀 위험 (RUNBOOK §9 참조).
