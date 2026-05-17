# lite_server 자동 재시작 watchdog — cloudflared_watchdog 동일 패턴 (자원 최소)
# WaitForExit() = 자식 프로세스 종료까지 PS 프로세스는 sleep (CPU 0%)
# 추가 안전장치: 5분 내 5회 이상 비정상 종료 → 60초 throttle (무한 재시작 방지)
$pyExe    = "C:\Users\leesc\Documents\Seoul\.venv\Scripts\python.exe"
$root     = "C:\Users\leesc\Documents\Seoul"
$runLog   = "C:\Users\leesc\Documents\Seoul\logs\lite_run.log"
$wdLog    = "C:\Users\leesc\Documents\Seoul\logs\lite_watchdog.log"
$lockFile = "C:\Users\leesc\Documents\Seoul\logs\lite_watchdog.lock"

# 단일 인스턴스 lock — 중복 실행 시 즉시 종료
$myPid = $PID
if (Test-Path $lockFile) {
    $existingPid = [int](Get-Content $lockFile -ErrorAction SilentlyContinue)
    if ($existingPid -and ($existingPid -ne $myPid)) {
        $proc = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
        if ($proc) {
            $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Add-Content $wdLog "$ts [lite-wd] duplicate detected (pid $existingPid) — exit"
            exit 0
        }
    }
}
$myPid | Set-Content $lockFile

# Failure throttle
$failures = New-Object System.Collections.Generic.Queue[datetime]
$MAX_FAILS = 5
$WINDOW_MIN = 5

try {
    while ($true) {
        $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Add-Content $wdLog "$ts [lite-wd] start lite_server :8766"
        $start = Get-Date
        $p = Start-Process -FilePath $pyExe `
            -ArgumentList @('-u','-m','src.cv.lite_server','--port','8766','--demo') `
            -WorkingDirectory $root `
            -RedirectStandardOutput $runLog `
            -WindowStyle Hidden -PassThru
        $p.WaitForExit()
        $duration = (Get-Date) - $start
        $ts2 = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Add-Content $wdLog "$ts2 [lite-wd] exit code=$($p.ExitCode) after $([int]$duration.TotalSeconds)s"

        # Failure throttle — 짧은 시간 내 다회 실패 시 대기
        $now = Get-Date
        $failures.Enqueue($now)
        while ($failures.Count -gt 0 -and ($now - $failures.Peek()).TotalMinutes -gt $WINDOW_MIN) {
            $failures.Dequeue() | Out-Null
        }
        if ($failures.Count -ge $MAX_FAILS) {
            Add-Content $wdLog "$ts2 [lite-wd] too many fails ($($failures.Count) in $WINDOW_MIN min) — cooldown 60s"
            Start-Sleep -Seconds 60
            $failures.Clear()
        } else {
            Start-Sleep -Seconds 5
        }
    }
} finally {
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
}
