"""
Venom Desktop Background Wake Service
======================================
Runs continuously in the background on Windows.
Listens for the wake word "Venom" or "Hey Venom".
When summoned:
  1. Plays the symbiotic awakening chime.
  2. Ensures Venom backend and frontend are running.
  3. Pops open a dedicated standalone Venom application window directly on screen.
  4. Greets the host aloud: "We are Venom. What do you require, host?"
  5. Immediately primes the UI to listen to your voice command!
"""

import os
import sys
import time
import socket
import urllib.request
import urllib.parse
import json
import webbrowser
import subprocess
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import speech_recognition as sr
from rich.console import Console

console = Console()

WAKE_WORDS = [
  "venom",
  "hey venom",
  "ok venom",
  "okay venom",
  "yo venom",
  "call venom",
  "wake up venom",
  "we are venom",
]

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

BACKEND_PORT = 7777
FRONTEND_PORT = 5173
COOLDOWN_SECONDS = 5.0


def is_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0


def ensure_backend_running():
    """Verify backend is alive; start it if not."""
    if not is_port_listening(BACKEND_PORT):
        console.print("[dim yellow]Starting Venom backend server...[/dim yellow]")
        python_exe = sys.executable
        main_py = BACKEND_DIR / "main.py"
        subprocess.Popen(
            [python_exe, str(main_py), "serve", "--host", "127.0.0.1", "--port", str(BACKEND_PORT)],
            cwd=str(BACKEND_DIR),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        for _ in range(20):
            time.sleep(0.4)
            if is_port_listening(BACKEND_PORT):
                break


def ensure_frontend_running():
    """Verify frontend is alive; start it if not."""
    if not is_port_listening(FRONTEND_PORT):
        console.print("[dim yellow]Starting Venom UI dev server...[/dim yellow]")
        frontend_dir = BACKEND_DIR.parent / "frontend"
        subprocess.Popen(
            "npm run dev -- --host 127.0.0.1",
            cwd=str(frontend_dir),
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        for _ in range(20):
            time.sleep(0.4)
            if is_port_listening(FRONTEND_PORT):
                break


def play_symbiote_chime():
    """Play awakening audio cue on Windows."""
    if os.name == "nt":
        try:
            import winsound
            winsound.Beep(440, 90)
            winsound.Beep(880, 160)
        except Exception:
            pass


def speak_greeting_local(phrase: str = "We are Venom. What do you require, host?"):
    """Vocalize greeting immediately through Windows SAPI speech if available."""
    if os.name == "nt":
        try:
            ps_cmd = f"Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Rate = -1; $synth.Speak('{phrase}');"
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            pass


def notify_backend_wake(command: str = ""):
    """Notify backend REST endpoint that Venom was awakened."""
    url = f"http://127.0.0.1:{BACKEND_PORT}/api/voice/wake"
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps({"command": command, "phrase": "Venom"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=2.0)
    except Exception:
        pass


def launch_or_focus_venom_window(app_url: str):
    """
    Guarantees that a dedicated Venom window pops open on screen
    and receives foreground OS focus immediately.
    """
    # 1. If window is already open, activate and bring it to foreground
    if os.name == "nt":
        try:
            ps_script = (
                "$wshell = New-Object -ComObject Wscript.Shell; "
                "if ($wshell.AppActivate('VENOM')) { exit 0 } else { exit 1 }"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if res.returncode == 0:
                console.print("[bold green]✔ Brought existing Venom window to foreground.[/bold green]")
                return
        except Exception:
            pass

    # 2. Find Chrome or Edge to launch in standalone App Window mode
    browser_exe = None
    for p in BROWSER_CANDIDATES:
        if os.path.exists(p):
            browser_exe = p
            break

    console.print(f"[bold cyan]Opening Venom dedicated app window via {browser_exe or 'default browser'}...[/bold cyan]")

    if browser_exe:
        try:
            # --app creates a dedicated standalone app window without browser tabs
            # --new-window forces Windows to create and focus a new top-level window
            subprocess.Popen(
                [browser_exe, f"--app={app_url}", "--new-window"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )
            # Give the window 700ms to open and bring to front
            time.sleep(0.7)
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", "(New-Object -ComObject Wscript.Shell).AppActivate('VENOM')"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            return
        except Exception as e:
            console.print(f"[yellow]App mode launch failed ({e}), falling back...[/yellow]")

    # Fallback to standard browser open
    webbrowser.open_new(app_url)


def on_venom_called(recognized_text: str):
    """Triggered when wake word is detected."""
    console.print(f"\n[bold green]🕷️ VENOM CALLED BY HOST:[/bold green] \"{recognized_text}\"")

    # Extract command following the wake word
    lower = recognized_text.lower()
    command = ""
    for w in WAKE_WORDS:
        if w in lower:
            idx = lower.find(w)
            command = lower[idx + len(w):].strip(" ,.?!-")
            break

    # 1. Play immediate audio cue
    play_symbiote_chime()

    # 2. Ensure both servers are up before opening window
    ensure_backend_running()
    ensure_frontend_running()

    # 3. Notify backend
    notify_backend_wake(command)

    # 4. Open and focus window on screen
    query_params = {"wake": "true"}
    if command:
        query_params["cmd"] = command
    app_url = f"http://127.0.0.1:{FRONTEND_PORT}/?{urllib.parse.urlencode(query_params)}"

    launch_or_focus_venom_window(app_url)

    # 5. Speak greeting out loud immediately
    speak_greeting_local("We are Venom. What do you require, host?")


def start_wake_listener():
    """Main continuous background listening loop."""
    console.print(
        "[bold white]\n"
        "╔════════════════════════════════════════════════════════════════╗\n"
        "║            🕷️  VENOM DESKTOP BACKGROUND WAKE SERVICE            ║\n"
        "║                                                                ║\n"
        "║  Running in the background...                                  ║\n"
        "║  Say 'Venom' or 'Hey Venom' anytime to automatically           ║\n"
        "║  awaken and open the application hands-free.                   ║\n"
        "╚════════════════════════════════════════════════════════════════╝\n"
        "[/bold white]"
    )

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 400
    recognizer.pause_threshold = 0.8

    try:
        mic = sr.Microphone()
    except Exception as e:
        console.print(f"[bold red]Error accessing microphone:[/bold red] {e}")
        return

    console.print("[dim green]Calibrating microphone for ambient room noise...[/dim green]")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
    console.print("[bold green]✔ Symbiote ears active. Listening for 'Venom'...[/bold green]\n")

    last_trigger_time = 0.0

    while True:
        try:
            with mic as source:
                # Capture audio phrase
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=5.0)

            # Check cooldown
            if time.time() - last_trigger_time < COOLDOWN_SECONDS:
                continue

            # Transcribe phrase locally or via Google speech recognition
            try:
                text = recognizer.recognize_google(audio, language="en-US")
                lower = text.lower()
                console.print(f"[dim]Heard: \"{text}\"[/dim]")

                # Check if any wake word was spoken
                if any(w in lower for w in WAKE_WORDS):
                    last_trigger_time = time.time()
                    on_venom_called(text)

            except sr.UnknownValueError:
                # Speech was unintelligible, continue listening quietly
                pass
            except sr.RequestError:
                # Network glitch with speech endpoint, wait a moment
                time.sleep(1.0)

        except KeyboardInterrupt:
            console.print("\n[bold green]Venom background listener stopped.[/bold green]")
            break
        except Exception:
            time.sleep(0.5)


if __name__ == "__main__":
    start_wake_listener()
