"""
Venom Native Desktop Application
================================
Full-featured standalone Windows desktop application:
1. Safely redirects stdout/stderr when launched without a console (pythonw.exe).
2. Embeds the FastAPI kernel serving the built React UI and full laptop system APIs.
3. Launches a dedicated standalone desktop window (Chrome/Edge App mode: zero tabs, zero URL bar)
   with 100% native Microphone & Speech Recognition support.
4. Embeds continuous background voice wake listening ("Venom" wake word).
5. Lives in the Windows System Tray for instant reopen and voice access.
"""

from __future__ import annotations

import os
import sys
import time
import json
import socket
import urllib.request
import threading
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
LOG_FILE = ROOT_DIR / "desktop_app.log"

# Fix pythonw.exe crash where sys.stdout / sys.stderr are None
if sys.stdout is None:
    sys.stdout = open(LOG_FILE, "a", encoding="utf-8", buffering=1)
if sys.stderr is None:
    sys.stderr = open(LOG_FILE, "a", encoding="utf-8", buffering=1)

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from api.app import create_app
from core.config import VenomConfig

PORT = 7777
HOST = "127.0.0.1"
APP_URL = f"http://{HOST}:{PORT}/"

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def is_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    """Check if server port is already listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


def find_app_browser() -> str | None:
    """Find Chrome or Edge to render standalone Desktop App window."""
    for path in BROWSER_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def open_venom_window(url: str = APP_URL):
    """Open or bring to foreground the standalone Venom Desktop Window."""
    # 1. Check specifically for an already-open Chrome/Edge Venom App window
    if os.name == "nt":
        try:
            ps_script = (
                "$p = Get-Process chrome, msedge -ErrorAction SilentlyContinue | "
                "Where-Object { $_.MainWindowTitle -like '*VENOM — We Are Symbiote*' } | Select-Object -First 1; "
                "if ($p) { "
                "$wshell = New-Object -ComObject Wscript.Shell; "
                "if ($wshell.AppActivate($p.Id)) { exit 0 } "
                "} "
                "exit 1"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if res.returncode == 0:
                return
        except Exception:
            pass

    # 2. Launch standalone App Window (no tabs, no address bar, dedicated profile in LocalAppData)
    browser = find_app_browser()
    if browser:
        local_app_data = os.environ.get("LOCALAPPDATA")
        profile_dir = Path(local_app_data) / "VenomDesktopProfile" if local_app_data else (ROOT_DIR / ".venom_desktop_profile")
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        popen_kwargs: dict = {}
        if os.name == "nt":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 1  # SW_SHOWNORMAL
            popen_kwargs["startupinfo"] = si
            popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(
            [
                browser,
                f"--app={url}",
                f"--user-data-dir={profile_dir}",
                "--window-size=1240,820",
                "--new-window",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            **popen_kwargs,
        )
        # Ensure OS foreground activation
        if os.name == "nt":
            time.sleep(0.8)
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "(New-Object -ComObject Wscript.Shell).AppActivate('VENOM')"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            except Exception:
                pass
    else:
        import webbrowser
        webbrowser.open_new(url)


def start_backend_server():
    """Run uvicorn server serving frontend dist & full laptop APIs."""
    cfg = VenomConfig()
    app = create_app(cfg)
    config = uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        log_level="warning",
        use_colors=False,
    )
    server = uvicorn.Server(config)
    server.run()


def start_voice_wake_listener(on_wake_callback):
    """Background thread listening for 'Venom' wake word on laptop microphone."""
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8

        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)

        def audio_callback(rec, audio):
            try:
                text = rec.recognize_google(audio).lower().strip()
                if "venom" in text:
                    print(f"[WAKE] Heard: {text}")
                    on_wake_callback(text)
            except Exception:
                pass

        recognizer.listen_in_background(mic, audio_callback, phrase_time_limit=4)
        print("[OK] Background desktop microphone wake listener active.")
    except Exception as exc:
        print(f"[WARN] Voice wake listener warning: {exc}")


def run_tray_icon(stop_event: threading.Event):
    """Run Windows System Tray icon for Venom Desktop."""
    try:
        import pystray
        from PIL import Image

        ico_path = ROOT_DIR / "venom.ico"
        if ico_path.exists():
            icon_img = Image.open(ico_path)
        else:
            icon_img = Image.new("RGBA", (64, 64), (0, 255, 102, 255))

        def on_open(icon, item):
            open_venom_window(APP_URL)

        def on_quit(icon, item):
            icon.stop()
            stop_event.set()
            os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem("Open VENOM Desktop", on_open, default=True),
            pystray.MenuItem("Quit VENOM", on_quit),
        )
        tray = pystray.Icon("VENOM", icon_img, "VENOM Symbiotic AI", menu)
        tray.run()
    except Exception as exc:
        print(f"[WARN] System tray fallback: {exc}")
        while not stop_event.is_set():
            time.sleep(1)


def main():
    # If already running, just pop open the window and exit immediately
    if is_port_listening(PORT, HOST):
        print("Existing VENOM kernel detected. Opening desktop window...")
        open_venom_window(APP_URL)
        return

    print("Starting VENOM Desktop Application...")
    server_thread = threading.Thread(target=start_backend_server, daemon=True)
    server_thread.start()

    # Wait until local FastAPI server is accepting connections
    for _ in range(40):
        time.sleep(0.25)
        if is_port_listening(PORT, HOST):
            break

    def on_wake(heard_text: str):
        lower = heard_text.lower()
        idx = lower.find("venom")
        command = lower[idx + 5 :].strip(" ,.?!-") if idx != -1 else ""

        try:
            req = urllib.request.Request(
                f"http://{HOST}:{PORT}/api/voice/wake",
                data=json.dumps({"command": command, "phrase": "Venom"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=1.5)
        except Exception:
            pass

        # Play chime on Windows
        if os.name == "nt":
            try:
                import winsound
                winsound.Beep(620, 120)
                winsound.Beep(880, 180)
            except Exception:
                pass

        open_venom_window(f"{APP_URL}?wake=true")

    # Start background voice listener
    wake_thread = threading.Thread(target=start_voice_wake_listener, args=(on_wake,), daemon=True)
    wake_thread.start()

    # Open standalone desktop window right away!
    open_venom_window(APP_URL)

    # Keep alive in System Tray
    stop_event = threading.Event()
    run_tray_icon(stop_event)


if __name__ == "__main__":
    main()
