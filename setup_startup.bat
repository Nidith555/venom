@echo off
title Venom - Enable Run on Windows Startup
cd /d "%~dp0"
echo ==========================================================
echo       🕷️ VENOM AUTO-START SETUP FOR WINDOWS
echo ==========================================================
echo.
echo This script registers Venom's silent background listener
echo in your Windows Startup folder so Venom is always ready
echo to open and respond whenever you call "Venom"!
echo.

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_DIR%\VenomWakeService.lnk"
set "TARGET_VBS=%~dp0start_venom_silent.vbs"

echo Creating startup shortcut...
powershell -Command "$s = (New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%TARGET_VBS%'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Venom AI Symbiote Background Listener'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo.
    echo [SUCCESS] Venom will now automatically run quietly in the background on startup!
    echo Whenever you call "Venom", it will automatically awaken and open.
    echo.
) else (
    echo [ERROR] Could not create startup shortcut.
)
pause
