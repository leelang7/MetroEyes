@echo off
title MetroEyes - Live Monitor (Ctrl+C to exit)
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "while ($true) { Clear-Host; & '%~dp0scripts\metroeyes.ps1' status; Write-Host '----- backend.log (tail 8) -----' -ForegroundColor DarkGray; Get-Content '%~dp0logs\backend.log' -Tail 8 -ErrorAction SilentlyContinue; Write-Host ''; Write-Host 'Refresh in 5s (Ctrl+C exit)' -ForegroundColor DarkGray; Start-Sleep -Seconds 5 }"
