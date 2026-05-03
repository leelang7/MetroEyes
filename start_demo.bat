@echo off
REM MetroEyes demo launcher (double-click)
REM 모든 컴포넌트가 minimize 콘솔로 작업표시줄에 뜸 (화면 가림 X)
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File ".\scripts\start_demo.ps1" -IncludeStatic %*
echo.
echo Demo started. Press any key to close this window (services keep running).
pause >nul
