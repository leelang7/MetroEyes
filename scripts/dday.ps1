# MetroEyes D-day 통합 검증 스크립트 (cycle 395)
# 사용: .\scripts\dday.ps1 [--full | --quick | --regen]
#
# --quick (default): submission_check --ci + pytest 빠른 검증 (< 10 초)
# --full            : EDA 전체 재생성 + 풀 검증 (~3 분, D-1 권장)
# --regen           : EDA 재생성만 (canonical KPI 갱신 후 광고 자료 동기화 필요시)

param(
  [switch]$Full,
  [switch]$Quick,
  [switch]$Regen
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

function Write-Step($msg, $color = 'Cyan') {
  Write-Host ""
  Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor $color
  Write-Host " $msg" -ForegroundColor $color
  Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor $color
}

if (-not $Quick -and -not $Full -and -not $Regen) { $Quick = $true }

# ========== 모드 1: --regen — EDA 재생성 ==========
if ($Regen -or $Full) {
  Write-Step "1. EDA 재생성 (cycle 360 / 368 / 390 정책 ROI v3 + 호선 + CO₂)"
  python scripts/policy_roi_v3.py
  if ($LASTEXITCODE -ne 0) { Write-Host "❌ policy_roi_v3 실패" -ForegroundColor Red; exit 2 }
  python scripts/eda_line_priority_roi.py
  if ($LASTEXITCODE -ne 0) { Write-Host "❌ eda_line_priority_roi 실패" -ForegroundColor Red; exit 2 }
  python scripts/eda_line_hour_priority.py
  if ($LASTEXITCODE -ne 0) { Write-Host "❌ eda_line_hour_priority 실패" -ForegroundColor Red; exit 2 }
  python scripts/eda_co2_savings.py
  if ($LASTEXITCODE -ne 0) { Write-Host "❌ eda_co2_savings 실패" -ForegroundColor Red; exit 2 }
  Write-Host "✅ EDA 재생성 완료 — frontend/figs/*.json 업데이트" -ForegroundColor Green
}

# ========== 모드 2: 회귀 가드 ==========
Write-Step "2. 회귀 가드 (244+ tests)"
python -m pytest tests/ --ignore=tests/test_smoke.py -q
if ($LASTEXITCODE -ne 0) { Write-Host "❌ pytest 실패 — 수정 후 재실행" -ForegroundColor Red; exit 2 }

# ========== 모드 3: ship-gate ==========
if ($Full) {
  Write-Step "3. submission_check 풀 검증 (heavy import + pytest 포함, ~2분)"
  python scripts/submission_check.py
} else {
  Write-Step "3. submission_check --ci 빠른 검증 (1초 < 10 항목)"
  python scripts/submission_check.py --ci
}
$exit = $LASTEXITCODE

# ========== 결과 ==========
Write-Host ""
if ($exit -eq 0) {
  Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Green
  Write-Host "  ✅ ALL PASS — 제출 준비 완료 🎉" -ForegroundColor Green
  Write-Host "  다음 단계: docs/SUBMISSION_GUIDE.md §0~9 따라 PDF 변환 + 마이박스 제출" -ForegroundColor Green
  Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Green
} elseif ($exit -eq 1) {
  Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
  Write-Host "  ⚠️  WARN — 제출 가능 (위 WARN 항목 D-day 직전 점검 권장)" -ForegroundColor Yellow
  Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
} else {
  Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Red
  Write-Host "  ❌ FAIL — 위 항목 수정 필수" -ForegroundColor Red
  Write-Host "  복구: docs/RUNBOOK.md 9 시나리오 참조" -ForegroundColor Red
  Write-Host "════════════════════════════════════════════════════════════════════" -ForegroundColor Red
}

exit $exit
