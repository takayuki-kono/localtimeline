@echo off
rem Unattended (task scheduler) entry point.
rem Do NOT add `pause` here: it blocks scheduled runs forever.
cd /d "%~dp0"

setlocal enableextensions

rem Prefer Python launcher (task scheduler PATH-safe)
set "PY=python"
where py >nul 2>nul && set "PY=py -3"

echo ==========================================
echo [%date% %time%] run_analyze.bat start
echo ==========================================
echo Generating Focus Timeline Images and Syncing to Sheets...
%PY% process_focus_outputs.py
if errorlevel 1 (
    echo [%date% %time%] run_analyze.bat failed.
    exit /b 1
)

echo ==========================================
echo [%date% %time%] run_analyze.bat done.
exit /b 0
