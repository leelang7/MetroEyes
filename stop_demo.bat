@echo off
REM MetroEyes — stop all components (double-click)
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File ".\scripts\start_demo.ps1" -Stop
echo.
echo All components stopped.
pause
