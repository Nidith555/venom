@echo off
title VENOM Desktop AI
cd /d "%~dp0"
"backend\.venv\Scripts\python.exe" desktop_app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Venom Desktop encountered an error.
    pause
)
