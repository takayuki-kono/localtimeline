@echo off
cd /d "%~dp0"
python analyze_usage.py
python generate_focus_timeline.py
python sync_focus_to_sheet.py
exit
