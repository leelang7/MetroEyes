# MetroEyes 데모 한 번에 띄우기
#
# 사용법:
#   pwsh scripts\start_demo.ps1            # backend + publisher + ngrok 모두
#   pwsh scripts\start_demo.ps1 -NoNgrok   # 외부 노출 X (로컬/USB 데모만)
#   pwsh scripts\start_demo.ps1 -Stop      # 모두 종료
#
# 각 프로세스는 새 콘솔 창으로 떠서 stdout 직접 보임 (사용자가 진단 즉시 가능).
# Claude/sandbox에서 RedirectStandardOutput으로 child가 stuck하던 문제 회피.

param(
    [switch]$Stop,
    [switch]$NoNgrok,
    [string]$Model = "yolo11s.pt",
    [int]$Imgsz = 1280,
    [double]$Conf = 0.18,
    [int]$Port = 8765,
    [string]$Video = "test\vtest.avi"
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if ($Stop) {
    Write-Host "=== MetroEyes 데모 종료 ===" -ForegroundColor Yellow
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object {
        $_.CommandLine -match "tesla_bev|feed_video"
    } | ForEach-Object {
        Write-Host "  kill PID=$($_.ProcessId)  $($_.CommandLine.Substring(0,[Math]::Min(80,$_.CommandLine.Length)))..."
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
    Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  kill ngrok PID=$($_.Id)"
        Stop-Process -Id $_.Id -Force
    }
    Write-Host "[done]" -ForegroundColor Green
    exit 0
}

# 사전 점검
$venv = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venv)) { Write-Error ".venv 없음: $venv"; exit 1 }
if (-not (Test-Path (Join-Path $root $Video))) {
    Write-Warning "비디오 없음: $Video — publisher 띄우지 않음"
    $skipPub = $true
}

# 8765 이미 LISTEN인지
$existing = (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).OwningProcess
if ($existing) {
    Write-Warning "포트 $Port 이미 사용 중 (PID=$existing). 먼저 -Stop 하시거나 다른 포트 사용."
    Write-Host "  종료하려면: pwsh scripts\start_demo.ps1 -Stop" -ForegroundColor Yellow
    exit 1
}

Write-Host "=== MetroEyes 데모 기동 ===" -ForegroundColor Cyan
Write-Host "  root:  $root"
Write-Host "  model: $Model (imgsz=$Imgsz conf=$Conf port=$Port)"

# 1) 백엔드 (새 콘솔)
Write-Host ""
Write-Host "[1/3] backend 새 콘솔 띄움..." -ForegroundColor Cyan
$be = Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root'; & '$venv' -u -m src.cv.tesla_bev --port $Port --model '$Model' --imgsz $Imgsz --conf $Conf"
) -PassThru -WorkingDirectory $root
Write-Host "  backend PID=$($be.Id) — 그 콘솔에 [load] yolo... → ws://0.0.0.0:$Port 떠야 정상" -ForegroundColor Gray

# yolo 로딩 대기 (LISTEN 시작까지)
Write-Host "  포트 $Port LISTEN 대기 (최대 60s)..."
$listenOk = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 2
    $l = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($l) { $listenOk = $true; break }
}
if (-not $listenOk) {
    Write-Warning "60s 안에 backend가 listen 시작 못함. backend 콘솔에서 에러 확인."
    Write-Host "  backend 창의 마지막 출력을 보고 진행 결정." -ForegroundColor Yellow
} else {
    Write-Host "  backend LISTEN OK" -ForegroundColor Green
}

# 2) publisher (옵션)
if (-not $skipPub) {
    Write-Host ""
    Write-Host "[2/3] publisher 새 콘솔 띄움 ($Video)..." -ForegroundColor Cyan
    $pb = Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit", "-Command",
        "Set-Location '$root'; & '$venv' scripts\feed_video.py '$Video'"
    ) -PassThru -WorkingDirectory $root
    Write-Host "  publisher PID=$($pb.Id) — [tx] N frames sent 떠야 정상" -ForegroundColor Gray
}

# 3) ngrok (옵션)
if (-not $NoNgrok) {
    Write-Host ""
    Write-Host "[3/3] ngrok 새 콘솔 띄움..." -ForegroundColor Cyan
    $ng = Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit", "-Command",
        "ngrok http $Port"
    ) -PassThru -WorkingDirectory $root
    Write-Host "  ngrok PID=$($ng.Id) — 4040 포트에서 public URL 확인 가능" -ForegroundColor Gray
    Start-Sleep -Seconds 3
    try {
        $tunnels = Invoke-RestMethod 'http://127.0.0.1:4040/api/tunnels' -TimeoutSec 3
        $url = $tunnels.tunnels[0].public_url
        Write-Host "  public URL: $url" -ForegroundColor Green
        Write-Host "  → 폰 앱 연결: wss://$($url -replace '^https?://','')" -ForegroundColor Green
    } catch {
        Write-Host "  ngrok 4040 응답 없음 — 콘솔에서 직접 확인" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== 시연 화면 ===" -ForegroundColor Cyan
Write-Host "  운영자 3D BEV: file://$root\frontend\operator_web\realbev.html"
Write-Host "  운영자 콘솔:    file://$root\frontend\operator_web\index.html"
Write-Host "  시민 PWA:       file://$root\frontend\passenger_app\index.html"
Write-Host ""
Write-Host "  종료: pwsh scripts\start_demo.ps1 -Stop" -ForegroundColor Yellow
