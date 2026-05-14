@echo off
title MetroEyes - Stop Publisher
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0metroeyes.ps1" stop-pub
timeout /t 2 >nul
