# MetroEyes 운영 스크립트 — start / stop / status / logs
# 사용: .\scripts\metroeyes.ps1 [start|stop|status|logs|restart]
#  또는 더블클릭: start.bat / stop.bat / status.bat / logs.bat

param(
    [Parameter(Position=0)]
    [ValidateSet('start','stop','status','logs','restart','')]
    [string]$Action = 'status'
)

$ErrorActionPreference = 'SilentlyContinue'
$root = Split-Path -Parent $PSScriptRoot
if (-not $root -or -not (Test-Path "$root\src")) { $root = (Get-Location).Path }
Set-Location $root

$logsDir = "$root\logs"
if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir | Out-Null }

$pyExe   = "$root\.venv\Scripts\python.exe"
$pywExe  = "$root\.venv\Scripts\pythonw.exe"
$cfExe   = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"
if (-not (Test-Path $cfExe)) { $cfExe = "cloudflared" }

$backendLog = "$logsDir\backend.log"
$staticLog  = "$logsDir\static.log"
$tunnelLog  = "$logsDir\cloudflared.log"
$publisherLog = "$logsDir\publisher.log"
$pidFile    = "$logsDir\metroeyes.pids"

function Write-Color($text, $color) { Write-Host $text -ForegroundColor $color }
function Save-Pid($name, $pid) {
    "$name`:$pid" | Add-Content -Path $pidFile -Encoding UTF8
}
function Get-Pids {
    if (Test-Path $pidFile) {
        Get-Content $pidFile | ForEach-Object {
            if ($_ -match '^([^:]+):(\d+)$') {
                [pscustomobject]@{ Name = $matches[1]; Pid = [int]$matches[2] }
            }
        }
    }
}

function Test-Port($port) {
    $r = Test-NetConnection -ComputerName 127.0.0.1 -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue
    return $r
}

function Show-Status {
    Write-Host ""
    Write-Color "===== MetroEyes Status =====" Cyan
    $beListen = Test-Port 8765
    $ssListen = Test-Port 5173
    Write-Host ("  Backend  :8765   " ) -NoNewline
    if ($beListen) { Write-Color "LISTEN" Green } else { Write-Color "DOWN" Red }
    Write-Host ("  Static   :5173   ") -NoNewline
    if ($ssListen) { Write-Color "LISTEN" Green } else { Write-Color "DOWN" Red }

    $cf = Get-Process cloudflared -ErrorAction SilentlyContinue
    Write-Host ("  Cloudflared      ") -NoNewline
    if ($cf) { Write-Color "alive (pid $($cf.Id -join ','))" Green } else { Write-Color "down" Red }

    if ($beListen) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:8765/" -Method GET -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            Write-Host "  Backend HTTP     " -NoNewline
            Write-Color "$($r.StatusCode) (WS expects 426)" Green
        } catch {
            $sc = $_.Exception.Response.StatusCode.value__
            if ($sc) { Write-Host "  Backend HTTP     " -NoNewline; Write-Color "$sc (WS upgrade required - 정상)" Green }
        }
    }

    Write-Host ""
    Write-Color "  URLs" Gray
    Write-Host "    Demo  : https://leelang7.github.io/MetroEyes/"
    Write-Host "    Local : http://localhost:5173/frontend/operator_web/index.html"
    Write-Host "    Tunnel: https://app.allthatai.kr"
    Write-Host ""
    Write-Color "  Logs ($logsDir)" Gray
    foreach ($log in @($backendLog, $staticLog, $tunnelLog, $publisherLog)) {
        if (Test-Path $log) {
            $sz = (Get-Item $log).Length
            $name = Split-Path $log -Leaf
            Write-Host ("    {0,-22} {1,8} bytes" -f $name, $sz)
        }
    }
    Write-Host ""
}

function Start-Backend {
    if (Test-Port 8765) {
        Write-Color "  backend 이미 :8765 LISTEN — skip" Yellow
        return
    }
    # 기본 lite+demo 한 가지로 통일 — 일반 데모/개발/경진대회 전부 이 모드
    # full 모드(tesla_bev YOLO11)는 실 CCTV 연결할 때만 METROEYES_MODE=full 환경변수로 명시
    $mode = if ($env:METROEYES_MODE) { $env:METROEYES_MODE } else { 'lite' }
    if ($mode -eq 'full') {
        # torch/ultralytics 사전 점검 — 없으면 lite로 자동 fallback
        & $pywExe -c "import torch, ultralytics" 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Color "  torch/ultralytics 미설치 — lite로 자동 fallback (실 카메라 비활성)" Yellow
            $mode = 'lite'
        }
    }
    if ($mode -eq 'full') {
        Remove-Item $backendLog -Force -ErrorAction SilentlyContinue
        $device = if ($env:METROEYES_DEVICE) { $env:METROEYES_DEVICE } else { 'cuda' }
        Write-Host "  backend (full / tesla_bev YOLO11 / $device) 시작 ... " -NoNewline
        $args = @('-u','-m','src.cv.tesla_bev','--port','8765','--model','yolo11n.pt','--imgsz','640','--conf','0.18','--device',$device)
    } else {
        Write-Host "  backend (lite + demo / HTTP API + 시뮬 BEV) 시작 ... " -NoNewline
        $args = @('-u','-m','src.cv.lite_server','--port','8765','--demo')
    }
    $p = Start-Process -FilePath $pywExe -ArgumentList $args -WorkingDirectory $root -PassThru
    Save-Pid 'backend' $p.Id
    Write-Color "pid $($p.Id)" Green
}

function Start-Static {
    if (Test-Port 5173) {
        Write-Color "  static 이미 :5173 LISTEN — skip" Yellow
        return
    }
    Write-Host "  static :5173 시작 ... " -NoNewline
    # http.server 는 access log 를 stdout 에 찍는다.
    # pythonw 는 stdout=None → 첫 요청에서 print 시 broken pipe → connection drop.
    # python.exe + Start-Process -WindowStyle Hidden + stdout 파일 redirect.
    Remove-Item $staticLog -Force -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath $pyExe -ArgumentList @('-u','-m','http.server','5173') `
                       -WorkingDirectory $root `
                       -RedirectStandardOutput $staticLog `
                       -RedirectStandardError "$logsDir\static_err.log" `
                       -WindowStyle Hidden -PassThru
    Save-Pid 'static' $p.Id
    Write-Color "pid $($p.Id)" Green
}

function Start-Tunnel {
    if (Get-Process cloudflared -ErrorAction SilentlyContinue) {
        Write-Color "  cloudflared 이미 실행 중 — skip" Yellow
        return
    }
    if (-not (Test-Path "$root\cloudflared-config.yml")) {
        Write-Color "  cloudflared-config.yml 없음 — skip" Yellow
        return
    }
    Write-Host "  cloudflared watchdog 시작 ... " -NoNewline
    $watchdog = "$root\scripts\cloudflared_watchdog.ps1"
    $p = Start-Process -FilePath "powershell.exe" `
        -ArgumentList @("-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", $watchdog) `
        -WorkingDirectory $root -WindowStyle Hidden -PassThru
    Save-Pid 'cloudflared' $p.Id
    Start-Sleep -Seconds 3
    $cf = Get-Process cloudflared -ErrorAction SilentlyContinue
    if ($cf) { Write-Color "pid $($cf.Id) (watchdog pid $($p.Id))" Green }
    else     { Write-Color "watchdog pid $($p.Id) — tunnel connecting..." Yellow }
}

function Start-Publisher {
    if (-not (Test-Path "$root\scripts\feed_video.py")) { return }
    if (-not (Test-Port 8765)) { return }   # backend 살아있을 때만
    $running = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" `
               -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'feed_video' }
    if ($running) { Write-Color "  publisher 이미 실행 중 — skip" Yellow; return }
    Write-Host "  publisher 시작 ... " -NoNewline
    $p = Start-Process -FilePath $pyExe -ArgumentList @("$root\scripts\feed_video.py") -WorkingDirectory $root `
                       -RedirectStandardOutput $publisherLog -RedirectStandardError "$logsDir\publisher_err.log" `
                       -WindowStyle Hidden -PassThru
    Save-Pid 'publisher' $p.Id
    Write-Color "pid $($p.Id)" Green
}

function Stop-All {
    Write-Color "===== Stop =====" Yellow
    $pids = Get-Pids
    if ($pids) {
        foreach ($p in $pids) {
            try {
                $proc = Get-Process -Id $p.Pid -ErrorAction Stop
                Stop-Process -Id $p.Pid -Force -ErrorAction Stop
                Write-Host "  killed $($p.Name) pid $($p.Pid)"
            } catch { Write-Host "  $($p.Name) pid $($p.Pid) already gone" -ForegroundColor DarkGray }
        }
        Remove-Item $pidFile -ErrorAction SilentlyContinue
    } else {
        # pidfile 없으면 알려진 프로세스 직접
        $stale = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe' OR Name='cloudflared.exe'" `
                 -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -match 'tesla_bev|http\.server|feed_video|cloudflared-config'
        }
        foreach ($p in $stale) {
            try {
                Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
                Write-Host "  killed $($p.Name) pid $($p.ProcessId)"
            } catch {}
        }
    }
    Write-Color "stopped." Green
}

function Show-Logs {
    if (-not (Test-Path $backendLog)) { New-Item -ItemType File -Path $backendLog | Out-Null }
    Write-Color "===== backend.log (Ctrl+C 종료) =====" Cyan
    Write-Host ""
    Get-Content $backendLog -Tail 20 -Wait
}

# ===== dispatch =====
switch ($Action) {
    'start' {
        Write-Color "===== MetroEyes Start =====" Cyan
        Start-Backend
        Start-Static
        Start-Tunnel
        Write-Host ""
        Write-Host "  backend 모델 로딩 ~30초 대기 중..." -ForegroundColor Gray
        Start-Sleep -Seconds 12
        # publisher (실 카메라 영상 송신) — 기본 OFF, METROEYES_PUBLISHER=1 또는 'start-pub' 액션으로만 시작
        # realbev 페이지가 브라우저에서 직접 frame 송신하므로 평소엔 불필요
        if ($env:METROEYES_PUBLISHER -eq '1') { Start-Publisher }
        else { Write-Color "  publisher skip (수동: scripts\start_publisher.bat 또는 METROEYES_PUBLISHER=1)" DarkGray }
        Show-Status
    }
    'start-pub'  { Start-Publisher; Show-Status }
    'stop-pub'   {
        $pubProcs = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue |
                    Where-Object { $_.CommandLine -match 'feed_video' }
        foreach ($p in $pubProcs) {
            try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop; Write-Host "  killed publisher pid $($p.ProcessId)" }
            catch {}
        }
        if (-not $pubProcs) { Write-Color "  publisher not running" Yellow }
    }
    'stop'    { Stop-All; Show-Status }
    'restart' { Stop-All; Start-Sleep -Seconds 2; & $PSCommandPath start }
    'logs'    { Show-Logs }
    default   { Show-Status }
}
