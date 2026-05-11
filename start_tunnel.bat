@echo off
taskkill /F /IM cloudflared.exe >nul 2>&1
start "" powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\Users\leesc\Documents\Seoul\scripts\cloudflared_watchdog.ps1"
echo CloudFlare watchdog started.
timeout /t 3 /nobreak >nul
