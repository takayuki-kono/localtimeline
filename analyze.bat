@echo off
cd /d "%~dp0"

setlocal enableextensions

rem Prefer Python launcher (task scheduler PATH-safe)
set "PY=python"
where py >nul 2>nul && set "PY=py -3"

echo ==========================================
echo Generating Focus Timeline Images and Syncing to Sheets...
%PY% process_focus_outputs.py
if errorlevel 1 goto :error

echo ==========================================
echo Analysis Workflow Complete.
pause
exit /b 0

:error
echo.
echo [ERROR] analyze.bat failed. Please check the output above.
pause
exit /b 1
