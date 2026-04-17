@echo off
cd /d "%~dp0"

setlocal enableextensions

rem Prefer Python launcher (task scheduler PATH-safe)
set "PY=python"
where py >nul 2>nul && set "PY=py -3"

echo ==========================================
echo Starting Usage Analysis...
%PY% analyze_usage.py
if errorlevel 1 goto :error

echo ==========================================
echo Generating Timeline Images...
%PY% generate_timeline.py
if errorlevel 1 goto :error
%PY% process_focus_outputs.py
if errorlevel 1 goto :error

echo ==========================================
echo Syncing Focus Time to Sheets...
echo (Handled by process_focus_outputs.py)

echo ==========================================
echo Generating Diary (in D:\tendency)...
cd /d "D:\tendency"
%PY% generate_diary.py
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
