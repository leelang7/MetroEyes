#!/usr/bin/env bash
# MetroEyes D-day 통합 검증 스크립트 (cycle 412 — Mac/Linux mirror of dday.ps1)
# 사용: ./scripts/dday.sh [--full | --quick | --regen]
#
# --quick (default): submission_check --ci + pytest 빠른 검증 (< 10 초)
# --full            : EDA 전체 재생성 + 풀 검증 (~3 분, D-1 권장)
# --regen           : EDA 재생성만 (canonical KPI 갱신 후 광고 자료 동기화 필요시)

set -euo pipefail

# 모드 파싱
MODE="quick"
case "${1:-}" in
  --full|-Full)   MODE="full";;
  --regen|-Regen) MODE="regen";;
  --quick|-Quick) MODE="quick";;
  "")             MODE="quick";;
  *)              echo "Unknown mode: $1 (use --quick / --full / --regen)"; exit 1;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

step() {
  echo
  echo "===================================================================="
  echo " $1"
  echo "===================================================================="
}

# ========== 모드 1: --regen — EDA 재생성 ==========
if [[ "$MODE" == "regen" || "$MODE" == "full" ]]; then
  step "1. EDA 재생성 (cycle 360 / 368 / 390 정책 ROI v3 + 호선 + CO₂)"
  python3 scripts/policy_roi_v3.py
  python3 scripts/eda_line_priority_roi.py
  python3 scripts/eda_line_hour_priority.py
  python3 scripts/eda_co2_savings.py
  echo "✅ EDA 재생성 완료 — frontend/figs/*.json 업데이트"
fi

# ========== 모드 2: 회귀 가드 ==========
step "2. 회귀 가드 (243+ tests)"
python3 -m pytest tests/ --ignore=tests/test_smoke.py -q

# ========== 모드 3: ship-gate ==========
if [[ "$MODE" == "full" ]]; then
  step "3. submission_check 풀 검증 (heavy import + pytest 포함, ~2분)"
  python3 scripts/submission_check.py
else
  step "3. submission_check --ci 빠른 검증 (1초 < 10 항목)"
  python3 scripts/submission_check.py --ci
fi
EXIT=$?

# ========== 결과 ==========
echo
if [[ $EXIT -eq 0 ]]; then
  echo "===================================================================="
  echo "  ✅ ALL PASS — 제출 준비 완료 🎉"
  echo "  다음 단계: docs/SUBMISSION_GUIDE.md §0~9 따라 PDF 변환 + 마이박스 제출"
  echo "===================================================================="
elif [[ $EXIT -eq 1 ]]; then
  echo "===================================================================="
  echo "  ⚠️  WARN — 제출 가능 (위 WARN 항목 D-day 직전 점검 권장)"
  echo "===================================================================="
else
  echo "===================================================================="
  echo "  ❌ FAIL — 위 항목 수정 필수"
  echo "  복구: docs/RUNBOOK.md 9 시나리오 참조"
  echo "===================================================================="
fi

exit $EXIT
