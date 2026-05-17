@echo off
title MetroEyes - Lite Watchdog
start "" /b powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0lite_server_watchdog.ps1"
echo lite_server_watchdog started (hidden). 자동 재시작 활성화됨.
timeout /t 3 >nul
