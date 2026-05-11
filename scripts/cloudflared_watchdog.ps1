$cfExe  = "C:\Users\leesc\AppData\Local\Microsoft\WinGet\Links\cloudflared.exe"
$config = "C:\Users\leesc\Documents\Seoul\cloudflared-config.yml"
$cfLog  = "C:\Users\leesc\Documents\Seoul\logs\cloudflared.err.log"
$wdLog  = "C:\Users\leesc\Documents\Seoul\logs\cloudflared_watchdog.log"

while ($true) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $wdLog "$ts [watchdog] start"
    & $cfExe tunnel --config $config run 2>&1 | Tee-Object -FilePath $cfLog -Append
    $ts2 = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $wdLog "$ts2 [watchdog] exit $LASTEXITCODE -- restart 5s"
    Start-Sleep -Seconds 5
}
