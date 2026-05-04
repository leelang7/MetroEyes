# MetroEyes demo launcher
#
# Usage (PowerShell 5.1 or 7):
#   .\scripts\start_demo.ps1                  # backend + publisher + cloudflared tunnel (minimized)
#   .\scripts\start_demo.ps1 -IncludeStatic   # + static file server :5173
#   .\scripts\start_demo.ps1 -Visible         # show consoles
#   .\scripts\start_demo.ps1 -NoTunnel        # local/USB only (no external)
#   .\scripts\start_demo.ps1 -Stop            # kill all
#
# Each component runs in its own console window so stdout is visible to the user.
# Default WindowStyle = Minimized so windows live in the taskbar, not on screen.

param(
    [switch]$Stop,
    [switch]$NoTunnel,
    [switch]$Visible,
    [switch]$IncludeStatic,
    [string]$Model = "yolo11n.pt",
    [int]$Imgsz = 640,
    [double]$Conf = 0.18,
    [int]$Port = 8765,
    [string]$Video = "test\vtest.avi"
)
$WS = if ($Visible) { 'Normal' } else { 'Minimized' }

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if ($Stop) {
    Write-Host "=== MetroEyes Stop ===" -ForegroundColor Yellow
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
        $_.CommandLine -match "tesla_bev|feed_video|http\.server"
    } | ForEach-Object {
        Write-Host "  kill PID=$($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  kill cloudflared PID=$($_.Id)"
        Stop-Process -Id $_.Id -Force
    }
    Write-Host "[done]" -ForegroundColor Green
    exit 0
}

# Pre-checks
$venv = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venv)) { Write-Error "venv not found: $venv"; exit 1 }
if (-not (Test-Path (Join-Path $root $Video))) {
    Write-Warning "video not found: $Video - publisher skipped"
    $skipPub = $true
}

$existing = (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).OwningProcess
if ($existing) {
    Write-Warning "port $Port already in use (PID=$existing). Run -Stop first."
    exit 1
}

Write-Host "=== MetroEyes Start ===" -ForegroundColor Cyan
Write-Host "  root:  $root"
Write-Host "  model: $Model (imgsz=$Imgsz conf=$Conf port=$Port window=$WS)"

# 1) backend
Write-Host ""
Write-Host "[1] backend (new console, $WS)..." -ForegroundColor Cyan
$be = Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root'; & '$venv' -u -m src.cv.tesla_bev --port $Port --model '$Model' --imgsz $Imgsz --conf $Conf"
) -PassThru -WorkingDirectory $root -WindowStyle $WS
Write-Host "  backend PID=$($be.Id)" -ForegroundColor Gray

# wait for LISTEN
Write-Host "  waiting for port $Port LISTEN (up to 60s)..."
$listenOk = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    $l = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($l) { $listenOk = $true; break }
}
if (-not $listenOk) {
    Write-Warning "backend did not start LISTEN within 60s - check the backend window."
} else {
    Write-Host "  backend LISTEN OK" -ForegroundColor Green
}

# 2) publisher
if (-not $skipPub) {
    Write-Host ""
    Write-Host "[2] publisher (new console, $WS)..." -ForegroundColor Cyan
    $pb = Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$root'; & '$venv' scripts\feed_video.py '$Video'"
    ) -PassThru -WorkingDirectory $root -WindowStyle $WS
    Write-Host "  publisher PID=$($pb.Id)" -ForegroundColor Gray
}

# 3) Cloudflare named tunnel — cloudflared-config.yml 있을 때만
if (-not $NoTunnel) {
    $cfConfig = Join-Path $root "cloudflared-config.yml"
    if (Test-Path $cfConfig) {
        Write-Host ""
        Write-Host "[3] cloudflared named tunnel (new console, $WS)..." -ForegroundColor Cyan
        $cfp = Start-Process -FilePath "powershell.exe" -ArgumentList @(
            "-NoExit", "-Command",
            "cloudflared tunnel --config '$cfConfig' run"
        ) -PassThru -WorkingDirectory $root -WindowStyle $WS
        Write-Host "  cloudflared PID=$($cfp.Id) - permanent domain (config in $cfConfig)" -ForegroundColor Gray
    } else {
        Write-Host ""
        Write-Host "[3] cloudflared SKIP - run setup_cloudflared.ps1 first to create config." -ForegroundColor Yellow
        Write-Host "    .\scripts\setup_cloudflared.ps1 -Domain app.YOUR-DOMAIN" -ForegroundColor Yellow
    }
}

# 4) static (optional)
if ($IncludeStatic) {
    Write-Host ""
    Write-Host "[4] static file server :5173 (new console, $WS)..." -ForegroundColor Cyan
    $ss = Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$root'; & '$venv' -m http.server 5173"
    ) -PassThru -WorkingDirectory $root -WindowStyle $WS
    Write-Host "  static PID=$($ss.Id) - http://localhost:5173/" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Demo URLs ===" -ForegroundColor Cyan
Write-Host "  Operator 3D BEV: file://$root\frontend\operator_web\realbev.html"
Write-Host "  Operator Subway: file://$root\frontend\operator_web\index.html"
Write-Host "  Citizen PWA:     file://$root\frontend\passenger_app\index.html"
Write-Host ""
Write-Host "  Stop: .\scripts\start_demo.ps1 -Stop" -ForegroundColor Yellow
