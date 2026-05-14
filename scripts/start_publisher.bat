@echo off
title MetroEyes - Start Publisher
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0metroeyes.ps1" start-pub
timeout /t 3 >nul
