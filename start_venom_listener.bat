@echo off
title Venom Desktop Background Wake Service
cd /d "%~dp0backend"
echo ===================================================
echo     🕷️ VENOM DESKTOP BACKGROUND WAKE SERVICE
echo ===================================================
echo.
echo Starting background voice listener...
echo Say "Venom" or "Hey Venom" to automatically wake and open the assistant.
echo.
".venv\Scripts\python.exe" venom_wake_service.py
pause
