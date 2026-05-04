@echo off
title MetroEyes - Logs (Ctrl+C to exit)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\metroeyes.ps1" logs
