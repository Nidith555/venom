"""
Venom Laptop & System Tools
===========================
Gives Venom autonomous system access to the host machine:
- Execute terminal / PowerShell commands
- Read, write, and explore files and directories
- Inspect laptop vitals (CPU, RAM, Disk, OS, battery)
- Open applications, folders, and web links on the machine
"""

from __future__ import annotations

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path
from typing import Any


def execute_terminal_command(command: str, timeout: int = 25) -> dict[str, Any]:
    """Execute a shell or PowerShell command on the host machine."""
    cmd_str = command.strip()
    if not cmd_str:
        return {"success": False, "error": "Empty command provided."}

    shell_cmd: list[str]
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
        
        # Limit output length to prevent context explosion
        if len(stdout) > 4000:
            stdout = stdout[:4000] + "\n...[Output truncated at 4000 characters]"
        if len(stderr) > 2000:
            stderr = stderr[:2000] + "\n...[Errors truncated]"

        return {
            "success": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": stdout or "(no stdout)",
            "stderr": stderr,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout} seconds."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def read_file(path: str, max_chars: int = 8000) -> dict[str, Any]:
    """Read contents of a file on the host machine."""
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


def list_directory(path: str = ".") -> dict[str, Any]:
    """List contents of a directory on the host machine."""
    try:
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
                })
            except Exception:
                continue

        # Sort directories first, then alphabetical
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return {
            "success": True,
            "path": str(p),
            "total_items": len(items),
            "items": items[:100],  # Limit to 100 entries
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def system_vitals() -> dict[str, Any]:
    """Inspect laptop vitals: OS, user, drives, RAM, and active processes."""
    vitals: dict[str, Any] = {
        "os": platform.platform(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "user": os.getenv("USERNAME") or os.getenv("USER") or "host",
        "hostname": platform.node(),
    }

    # Disk usage
    try:
        total, used, free = shutil.disk_usage(".")
        vitals["disk"] = {
            "total_gb": round(total / (1024**3), 1),
            "used_gb": round(used / (1024**3), 1),
            "free_gb": round(free / (1024**3), 1),
            "percent_free": round((free / total) * 100, 1),
        }
    except Exception:
        pass

    # Windows-specific system inspection via PowerShell
    if os.name == "nt":
        try:
            ps_script = (
                "$os = Get-CimInstance Win32_OperatingSystem; "
                "$cs = Get-CimInstance Win32_ComputerSystem; "
                "$freeMem = [math]::Round($os.FreePhysicalMemory / 1024, 0); "
                "$totalMem = [math]::Round($cs.TotalPhysicalMemory / 1048576, 0); "
                "$cpu = (Get-CimInstance Win32_Processor).Name; "
                "@{ FreeMemMB=$freeMem; TotalMemMB=$totalMem; CPU=$cpu } | ConvertTo-Json -Compress"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout.strip())
                vitals["hardware"] = data
        except Exception:
            pass

    return {"success": True, "vitals": vitals}


def open_application(target: str) -> dict[str, Any]:
    """Launch an application or open a file/folder in Explorer."""
    tgt = target.strip()
    if not tgt:
        return {"success": False, "error": "Target not provided"}

    try:
        if os.name == "nt":
            os.startfile(tgt)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", tgt])
        else:
            subprocess.Popen(["xdg-open", tgt])
        return {"success": True, "message": f"Opened '{tgt}' successfully."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
