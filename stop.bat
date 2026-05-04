@echo off
title MetroEyes - Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\metroeyes.ps1" stop
timeout /t 3 >nul
