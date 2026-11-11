"""
Venom Native Desktop Application
================================
Full-featured standalone Windows desktop application:
1. Embeds the FastAPI kernel serving the UI and all system APIs.
2. Embeds continuous background voice wake listening ("Venom" wake word).
3. Opens a native desktop window with full access to laptop files, apps, and terminal.
4. Provides system tray support.
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

# Ensure root & backend directories are in python path
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from api.app import create_app
from core.config import VenomConfig

PORT = 7777
HOST = "127.0.0.1"


def is_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    """Check if server port is already listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


def start_backend_server():
    """Run uvicorn server serving frontend dist & APIs."""
    cfg = VenomConfig()
    app = create_app(cfg)
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    server.run()


def start_voice_wake_listener(on_wake_callback=None):
    """Background thread listening for 'Venom' wake word."""
    try:
        import speech_recognition as sr
        from agent.laptop_tools import execute_terminal_command

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
                    print(f"\n🕷️ VENOM WAKE WORD DETECTED: {text}")
                    if on_wake_callback:
                        on_wake_callback(text)
            except Exception:
                pass

        recognizer.listen_in_background(mic, audio_callback, phrase_time_limit=4)
        print("✔ Background desktop microphone wake listener active.")
    except Exception as exc:
        print(f"Voice wake listener warning (non-fatal): {exc}")


def main():
    print("=" * 60)
    print("      🕷️ VENOM DESKTOP APPLICATION STARTING")
    print("=" * 60)

    # 1. Start backend server in daemon thread if not already running
    if not is_port_listening(PORT, HOST):
        print("Starting embedded Venom symbiote kernel on port 7777...")
        server_thread = threading.Thread(target=start_backend_server, daemon=True)
        server_thread.start()

        # Wait until backend is ready
        for _ in range(30):
            time.sleep(0.3)
            if is_port_listening(PORT, HOST):
                break
    else:
        print("Existing Venom symbiote kernel detected on port 7777.")

    app_url = f"http://{HOST}:{PORT}/"
    desktop_window = None

    def on_wake(heard_text: str):
        nonlocal desktop_window
        # Extract command after wake word
        lower = heard_text.lower()
        idx = lower.find("venom")
        command = lower[idx + 5:].strip(" ,.?!-") if idx != -1 else ""

        # Notify backend wake endpoint so UI automatically starts voice mode / responds
        try:
            req = urllib.request.Request(
                f"http://{HOST}:{PORT}/api/voice/wake",
                data=json.dumps({"command": command, "phrase": "Venom"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=1.5)
        except Exception:
            pass

        # Bring native window to front
        if desktop_window:
            try:
                desktop_window.restore()
                desktop_window.show()
            except Exception:
                pass
        if os.name == "nt":
            try:
                ps = "$wshell = New-Object -ComObject Wscript.Shell; $wshell.AppActivate('VENOM')"
                subprocess.run(["powershell", "-NoProfile", "-Command", ps], creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                pass

    # 2. Start background voice wake listener
    wake_thread = threading.Thread(target=start_voice_wake_listener, args=(on_wake,), daemon=True)
    wake_thread.start()

    # 3. Launch native desktop window via pywebview
    try:
        import webview

        print("Launching native Venom desktop window...")
        desktop_window = webview.create_window(
            title="VENOM — Symbiotic Intelligence",
            url=app_url,
            width=1240,
            height=820,
            min_size=(900, 600),
            background_color="#000000",
            text_select=True,
        )
        webview.start(debug=False)
    except Exception as e:
        print(f"pywebview notice ({e}). Falling back to standalone Chrome/Edge app window...")
        # Fallback to Chromium standalone app window mode
        browser_candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ]
        launched = False
        for b in browser_candidates:
            if os.path.exists(b):
                subprocess.Popen([b, f"--app={app_url}", "--window-size=1240,820", "--new-window"])
                launched = True
                break
        if not launched:
            import webbrowser
            webbrowser.open_new(app_url)

        # Keep server running in foreground
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nVenom desktop shut down.")


if __name__ == "__main__":
    main()
