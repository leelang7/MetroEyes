@echo off
title MetroEyes - Status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\metroeyes.ps1" status
echo.
pause
