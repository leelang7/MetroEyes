@echo off
title MetroEyes — Cloudflare Tunnel
echo [MetroEyes] cloudflared watchdog 시작 중...
taskkill /IM cloudflared.exe /F >nul 2>&1
timeout /t 1 /nobreak >nul
wscript.exe "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MetroEyes-cloudflared.vbs"
echo [MetroEyes] cloudflared watchdog 시작됨 (백그라운드 자동 재시작).
echo 로그: logs\cloudflared_watchdog.log
timeout /t 4 /nobreak >nul
