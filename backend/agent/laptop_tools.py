"""
Venom Laptop & System Tools
===========================
Gives Venom complete autonomous access to the host Windows/desktop machine:
- Discover and launch any installed application (Start Menu, Store apps, EXE, URLs)
- Close or inspect running applications & processes
- Search, read, write, create folders, move, or delete files across all user drives & folders
- Execute terminal / PowerShell commands
- Inspect laptop vitals (CPU, RAM, Disk, OS, battery)
"""

from __future__ import annotations

import os
import sys
import json
import shutil
import platform
import subprocess
from pathlib import Path
from typing import Any


def get_user_folders() -> dict[str, str]:
    """Return resolved paths to standard Windows/User directories."""
    home = Path.home()
    onedrive = Path(os.environ.get("OneDrive", str(home / "OneDrive")))
    candidates = {
        "home": home,
        "desktop": onedrive / "Desktop" if (onedrive / "Desktop").exists() else home / "Desktop",
        "documents": onedrive / "Documents" if (onedrive / "Documents").exists() else home / "Documents",
        "downloads": home / "Downloads",
        "pictures": onedrive / "Pictures" if (onedrive / "Pictures").exists() else home / "Pictures",
        "music": home / "Music",
        "videos": home / "Videos",
        "onedrive": onedrive,
    }
    return {k: str(v) for k, v in candidates.items() if v.exists()}


def execute_terminal_command(command: str, timeout: int = 30) -> dict[str, Any]:
    """Execute a shell or PowerShell command on the host machine."""
    cmd_str = command.strip()
    if not cmd_str:
        return {"success": False, "error": "Empty command provided."}

    if os.name == "nt":
        shell_cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd_str]
    else:
        shell_cmd = ["/bin/bash", "-c", cmd_str]

    try:
        proc = subprocess.run(
            shell_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        if len(stdout) > 5000:
            stdout = stdout[:5000] + "\n...[Output truncated at 5000 characters]"
        if len(stderr) > 2000:
            stderr = stderr[:2000] + "\n...[Errors truncated]"

        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": stdout or "(completed cleanly with no output)",
            "stderr": stderr,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout} seconds."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def read_file(path: str, max_chars: int = 12000) -> dict[str, Any]:
    """Read contents of any file on the host machine."""
    try:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"success": False, "error": f"File does not exist: {p}"}
        if p.is_dir():
            return {"success": False, "error": f"Path is a directory, not a file: {p}"}

        text = p.read_text(encoding="utf-8", errors="replace")
        truncated = False
        if len(text) > max_chars:
            text = text[:max_chars]
            truncated = True

        return {
            "success": True,
            "path": str(p),
            "size_bytes": p.stat().st_size,
            "truncated": truncated,
            "content": text,
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def write_file(path: str, content: str) -> dict[str, Any]:
    """Create or overwrite a file on the host machine."""
    try:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {
            "success": True,
            "path": str(p),
            "bytes_written": len(content.encode("utf-8")),
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def create_folder(path: str) -> dict[str, Any]:
    """Create a directory (and parents if needed)."""
    try:
        p = Path(path).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return {"success": True, "path": str(p)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def move_or_rename(source: str, destination: str) -> dict[str, Any]:
    """Move or rename a file or folder."""
    try:
        src = Path(source).expanduser().resolve()
        dst = Path(destination).expanduser().resolve()
        if not src.exists():
            return {"success": False, "error": f"Source not found: {src}"}
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return {"success": True, "source": str(src), "destination": str(dst)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def list_directory(path: str = ".") -> dict[str, Any]:
    """List contents of any directory on the host machine."""
    try:
        # Handle friendly folder names
        folders = get_user_folders()
        lower = path.strip().lower()
        if lower in folders:
            p = Path(folders[lower])
        else:
            p = Path(path).expanduser().resolve()

        if not p.exists():
            return {"success": False, "error": f"Path does not exist: {p}"}
        if not p.is_dir():
            return {"success": False, "error": f"Path is not a directory: {p}"}

        items = []
        for entry in p.iterdir():
            try:
                is_dir = entry.is_dir()
                size = 0 if is_dir else entry.stat().st_size
                items.append({
                    "name": entry.name,
                    "is_dir": is_dir,
                    "size_bytes": size,
                    "path": str(entry),
                })
            except Exception:
                continue

        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return {
            "success": True,
            "path": str(p),
            "total_items": len(items),
            "items": items[:150],
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def search_files(query: str, directory: str = "") -> dict[str, Any]:
    """Search for files matching query across user folders or a specified directory."""
    q = query.strip().lower()
    if not q:
        return {"success": False, "error": "Search query cannot be empty."}

    folders = get_user_folders()
    if directory:
        dir_lower = directory.strip().lower()
        roots = [Path(folders[dir_lower])] if dir_lower in folders else [Path(directory).expanduser().resolve()]
    else:
        roots = [Path(folders[k]) for k in ("desktop", "documents", "downloads", "onedrive") if k in folders]

    matches: list[dict[str, Any]] = []
    max_results = 60

    for root in roots:
        if not root.exists():
            continue
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                # Skip heavy system/dependency directories
                dirnames[:] = [
                    d for d in dirnames
                    if d not in {"node_modules", ".git", ".venv", "__pycache__", "AppData", "$RECYCLE.BIN"}
                ]
                for fn in filenames:
                    if q in fn.lower():
                        fp = Path(dirpath) / fn
                        try:
                            matches.append({
                                "name": fn,
                                "path": str(fp),
                                "size_bytes": fp.stat().st_size,
                            })
                        except Exception:
                            matches.append({"name": fn, "path": str(fp), "size_bytes": 0})
                        if len(matches) >= max_results:
                            return {"success": True, "query": query, "matches": matches, "truncated": True}
        except Exception:
            continue

    return {"success": True, "query": query, "matches": matches, "truncated": False}


def list_installed_apps() -> dict[str, Any]:
    """Discover installed applications on Windows via Start Menu & Store apps."""
    apps: dict[str, str] = {}

    if os.name == "nt":
        start_dirs = [
            Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        ]
        for sdir in start_dirs:
            if sdir.exists():
                for lnk in sdir.rglob("*.lnk"):
                    name = lnk.stem
                    if name.lower() not in apps and "uninstall" not in name.lower():
                        apps[name] = str(lnk)

        # Also query Windows Store / UWP apps via Get-StartApps
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-StartApps | Select-Object Name, AppID | ConvertTo-Json -Compress"],
                capture_output=True,
                text=True,
                timeout=6,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get("Name", "").strip()
                    appid = item.get("AppID", "").strip()
                    if name and appid and name not in apps:
                        apps[name] = f"shell:AppsFolder\\{appid}"
        except Exception:
            pass

    app_list = [{"name": k, "target": v} for k, v in sorted(apps.items(), key=lambda x: x[0].lower())]
    return {"success": True, "count": len(app_list), "apps": app_list[:150]}


def list_running_apps() -> dict[str, Any]:
    """List currently active windows and top memory processes."""
    if os.name != "nt":
        return {"success": False, "error": "Supported on Windows."}

    try:
        ps_cmd = (
            "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | "
            "Select-Object ProcessName, MainWindowTitle, Id, @{Name='MemMB';Expression={[math]::Round($_.WorkingSet64/1MB,1)}} | "
            "ConvertTo-Json -Compress"
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout.strip())
            if isinstance(data, dict):
                data = [data]
            return {"success": True, "running_apps": data}
        return {"success": True, "running_apps": []}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def open_application(target: str) -> dict[str, Any]:
    """
    Intelligently launch any installed app, folder, file, or URL on the laptop.
    Matches friendly names like 'spotify', 'vscode', 'downloads', 'chrome', etc.
    """
    tgt = target.strip()
    if not tgt:
        return {"success": False, "error": "Target not provided"}

    lower = tgt.lower()

    # 1. Check user folders (Desktop, Downloads, Documents, etc.)
    folders = get_user_folders()
    if lower in folders:
        try:
            os.startfile(folders[lower])
            return {"success": True, "message": f"Opened folder '{tgt}' ({folders[lower]})"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # 2. Check common built-in Windows aliases
    builtin_aliases = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "paint": "mspaint.exe",
        "cmd": "cmd.exe",
        "command prompt": "cmd.exe",
        "powershell": "powershell.exe",
        "terminal": "wt.exe",
        "windows terminal": "wt.exe",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "settings": "ms-settings:",
        "control panel": "control.exe",
        "vscode": "code",
        "vs code": "code",
        "visual studio code": "code",
        "chrome": "chrome.exe",
        "google chrome": "chrome.exe",
        "edge": "msedge.exe",
        "microsoft edge": "msedge.exe",
        "brave": "brave.exe",
    }

    if lower in builtin_aliases:
        alias_target = builtin_aliases[lower]
        try:
            if alias_target.endswith(":") or os.path.exists(alias_target):
                os.startfile(alias_target)
            else:
                subprocess.Popen(alias_target, shell=True)
            return {"success": True, "message": f"Launched '{tgt}' ({alias_target})."}
        except Exception:
            pass

    # 3. Direct path or URL
    if os.path.exists(tgt) or lower.startswith(("http://", "https://", "ms-")):
        try:
            os.startfile(tgt)
            return {"success": True, "message": f"Opened '{tgt}'."}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    # 4. Search installed apps from Start Menu & UWP Store apps
    if os.name == "nt":
        installed = list_installed_apps().get("apps", [])
        # Exact match first
        for app in installed:
            if app["name"].lower() == lower:
                try:
                    os.startfile(app["target"])
                    return {"success": True, "message": f"Launched installed app '{app['name']}'."}
                except Exception:
                    pass
        # Substring fuzzy match
        for app in installed:
            if lower in app["name"].lower():
                try:
                    os.startfile(app["target"])
                    return {"success": True, "message": f"Launched installed app '{app['name']}'."}
                except Exception:
                    pass

    # 5. Last resort shell start
    try:
        if os.name == "nt":
            subprocess.Popen(f'start "" "{tgt}"', shell=True)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", tgt])
        else:
            subprocess.Popen(["xdg-open", tgt])
        return {"success": True, "message": f"Attempted to open '{tgt}'."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def close_application(app_name: str) -> dict[str, Any]:
    """Close a running application by name."""
    if os.name != "nt":
        return {"success": False, "error": "Supported on Windows."}

    clean = app_name.strip().replace(".exe", "")
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Stop-Process -Name '*{clean}*' -Force -ErrorAction Stop"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if res.returncode == 0:
            return {"success": True, "message": f"Closed application matching '{clean}'."}
        return {"success": False, "error": res.stderr.strip() or f"No running process matched '{clean}'."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def system_vitals() -> dict[str, Any]:
    """Inspect laptop vitals: OS, user, drives, RAM, CPU, battery, and user folders."""
    vitals: dict[str, Any] = {
        "os": platform.platform(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "user": os.getenv("USERNAME") or os.getenv("USER") or "host",
        "hostname": platform.node(),
        "folders": get_user_folders(),
    }

    try:
        total, used, free = shutil.disk_usage("C:\\" if os.name == "nt" else ".")
        vitals["disk"] = {
            "total_gb": round(total / (1024**3), 1),
            "used_gb": round(used / (1024**3), 1),
            "free_gb": round(free / (1024**3), 1),
            "percent_free": round((free / total) * 100, 1),
        }
    except Exception:
        pass

    if os.name == "nt":
        try:
            ps_script = (
                "$os = Get-CimInstance Win32_OperatingSystem; "
                "$cs = Get-CimInstance Win32_ComputerSystem; "
                "$cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name; "
                "$bat = (Get-CimInstance Win32_Battery | Select-Object -First 1).EstimatedChargeRemaining; "
                "$freeMem = [math]::Round($os.FreePhysicalMemory / 1024, 0); "
                "$totalMem = [math]::Round($cs.TotalPhysicalMemory / 1048576, 0); "
                "@{ FreeMemMB=$freeMem; TotalMemMB=$totalMem; CPU=$cpu; BatteryPercent=$bat } | ConvertTo-Json -Compress"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=6,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if res.returncode == 0 and res.stdout.strip():
                vitals["hardware"] = json.loads(res.stdout.strip())
        except Exception:
            pass

    return {"success": True, "vitals": vitals}
