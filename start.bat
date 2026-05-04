@echo off
title MetroEyes - Start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\metroeyes.ps1" start
echo.
echo (this window auto-closes in 5s, or press any key to close now)
timeout /t 5 >nul
