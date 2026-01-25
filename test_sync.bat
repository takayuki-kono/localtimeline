@echo off
chcp 65001 > nul
cd /d %~dp0

echo --- Setting up dependencies ---
pip install gspread oauth2client
if %errorlevel% neq 0 (
    echo Error installing dependencies. Please check your python/pip setup.
    pause
    exit /b
)

echo.
echo --- Running Sync Script ---
python sync_focus_to_sheet.py

echo.
echo Done.
pause
