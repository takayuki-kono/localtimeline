@echo off
cd /d "%~dp0"

echo ==========================================
echo Starting Usage Analysis...
python analyze_usage.py

echo ==========================================
echo Generating Timeline Images...
python generate_timeline.py
python generate_focus_timeline.py

echo ==========================================
echo Syncing Focus Time to Sheets...
python sync_focus_to_sheet.py

echo ==========================================
echo Generating Diary (in D:\tendency)...
cd /d "D:\tendency"
python generate_diary.py

echo ==========================================
echo Analysis Workflow Complete.
pause
