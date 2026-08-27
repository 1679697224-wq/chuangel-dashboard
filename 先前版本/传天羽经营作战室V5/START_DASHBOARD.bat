@echo off
cd /d "%~dp0"
title Chuangel Executive Dashboard

where py >nul 2>nul
if errorlevel 1 goto no_python

echo Starting dashboard. The browser will open automatically...
echo Keep this window open while using the dashboard.
echo ------------------------------------------------------------
py -3 app.py
echo.
echo Dashboard stopped. Please send a screenshot if an error is shown above.
pause
exit /b 0

:no_python
echo Python 3 was not found.
echo Please install Python 3 and select "Add Python to PATH" during setup.
pause
exit /b 1
