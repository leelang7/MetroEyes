# Cloudflare named tunnel 자동 setup
#
# 사전 조건:
#   1. Cloudflare 계정 + 도메인 등록 완료 (DNS Cloudflare 사용 중)
#   2. cloudflared 설치 (winget install Cloudflare.cloudflared)
#   3. PowerShell 새 세션에서 실행 (PATH 갱신 후)
#
# 사용:
#   .\scripts\setup_cloudflared.ps1 -Domain app.metroeyes.app

param(
    [Parameter(Mandatory)] [string]$Domain,
    [string]$TunnelName = "metroeyes",
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# cloudflared 경로
$cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $cf) {
    $cf = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"
}
if (-not (Test-Path $cf)) { Write-Error "cloudflared not found. winget install Cloudflare.cloudflared"; exit 1 }
Write-Host "cloudflared: $cf"

# Step 1: 인증 (한 번만)
$cred = "$env:USERPROFILE\.cloudflared"
if (-not (Test-Path "$cred\cert.pem")) {
    Write-Host "[1/5] Cloudflare 인증 — 브라우저 자동 열림. 도메인 선택해 인증 완료." -ForegroundColor Cyan
    & $cf tunnel login
}

# Step 2: tunnel 생성 (또는 기존 가져오기)
$existing = & $cf tunnel list 2>$null | Select-String $TunnelName
if (-not $existing) {
    Write-Host "[2/5] tunnel 생성: $TunnelName" -ForegroundColor Cyan
    & $cf tunnel create $TunnelName
} else {
    Write-Host "[2/5] tunnel '$TunnelName' 이미 존재 — 재사용" -ForegroundColor Gray
}

# tunnel UUID 추출
$tunnelInfo = & $cf tunnel list 2>$null | Select-String $TunnelName | Select-Object -First 1
$uuid = ($tunnelInfo -split '\s+')[1]
if (-not $uuid) { Write-Error "tunnel UUID 추출 실패"; exit 1 }
Write-Host "  UUID: $uuid"

# Step 3: DNS 라우팅
Write-Host "[3/5] DNS 라우팅: $Domain → $TunnelName" -ForegroundColor Cyan
try {
    & $cf tunnel route dns $TunnelName $Domain
} catch {
    Write-Warning "DNS 라우팅 이미 존재 또는 실패. Cloudflare DNS에서 수동 확인."
}

# Step 4: config 생성
$configPath = "$root\cloudflared-config.yml"
@"
tunnel: $uuid
credentials-file: $cred\$uuid.json

ingress:
  - hostname: $Domain
    service: http://localhost:$Port
    originRequest:
      noTLSVerify: true
  - service: http_status:404
"@ | Out-File -FilePath $configPath -Encoding utf8
Write-Host "[4/5] config 작성: $configPath" -ForegroundColor Cyan

# Step 5: tunnel 시작 안내
Write-Host ""
Write-Host "[5/5] Setup 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "Tunnel 시작 (한 번):" -ForegroundColor Yellow
Write-Host "  cloudflared tunnel --config $configPath run $TunnelName"
Write-Host ""
Write-Host "또는 silent 백그라운드:" -ForegroundColor Yellow
Write-Host "  start_silent.vbs 안에 cloudflared 라인 추가됨 (다음 commit)"
Write-Host ""
Write-Host "검증:" -ForegroundColor Yellow
Write-Host "  curl https://$Domain"
Write-Host ""
Write-Host "다음:" -ForegroundColor Cyan
Write-Host "  frontend의 wss URL을 wss://$Domain 으로 일괄 교체 + git push"
