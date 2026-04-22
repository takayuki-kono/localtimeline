@echo off
rem Manual entry point. Delegates real work to run_analyze.bat
rem and pauses at the end so the user can read the output.
cd /d "%~dp0"

call "%~dp0run_analyze.bat"
set "RC=%errorlevel%"

if not "%RC%"=="0" (
    echo.
    echo [ERROR] analyze.bat failed (exit=%RC%). Please check the output above.
    pause
    exit /b %RC%
)

echo.
echo Analysis Workflow Complete.
pause
exit /b 0
