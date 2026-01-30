@echo off
cd /d "%~dp0"

echo Starting Screenpipe...
start "" ".\screenpipe_bin\bin\screenpipe.exe" --language japanese

echo Starting Pomodoro Timer...
start "Pomodoro" pythonw pomodoro.py

exit
