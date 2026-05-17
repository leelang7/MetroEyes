@echo off
title MetroEyes - Stop Lite Watchdog
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'lite_server_watchdog.ps1' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host \"killed watchdog pid $($_.ProcessId)\" }; Remove-Item 'C:\Users\leesc\Documents\Seoul\logs\lite_watchdog.lock' -Force -ErrorAction SilentlyContinue"
timeout /t 2 >nul
