$cfExe  = "C:\Users\leesc\AppData\Local\Microsoft\WinGet\Links\cloudflared.exe"
$config = "C:\Users\leesc\Documents\Seoul\cloudflared-config.yml"
$logFile = "C:\Users\leesc\Documents\Seoul\logs\cloudflared_watchdog.log"

while ($true) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $logFile "$ts [watchdog] cloudflared 시작"
    $p = Start-Process -FilePath $cfExe `
        -ArgumentList "tunnel --config `"$config`" run" `
        -WindowStyle Hidden -PassThru
    $p.WaitForExit()
    $ts2 = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $logFile "$ts2 [watchdog] cloudflared 종료 (exit $($p.ExitCode)) — 5초 후 재시작"
    Start-Sleep -Seconds 5
}
