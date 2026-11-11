"""
Venom File Uploads & System Access API Routes
==============================================
Provides endpoints for:
- Uploading files and documents from the frontend
- Direct laptop access (terminal command execution, file read/write, directory browse)
- System vitals telemetry (OS, disk, memory, CPU)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from agent.laptop_tools import (
    execute_terminal_command,
    list_directory,
    open_application,
    read_file,
    system_vitals,
    write_file,
)

router = APIRouter(prefix="/api", tags=["system", "files"])

# Upload storage directory
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class CommandRequest(BaseModel):
    command: str = Field(..., description="Terminal or PowerShell command to execute")
    timeout: int = Field(default=25, description="Timeout in seconds")


class FileReadRequest(BaseModel):
    path: str = Field(..., description="File path on the host machine to read")
    max_chars: int = Field(default=8000, description="Max characters to read")


class FileWriteRequest(BaseModel):
    path: str = Field(..., description="File path on the host machine to write")
    content: str = Field(..., description="Text content to write into the file")


class ListDirRequest(BaseModel):
    path: str = Field(default=".", description="Directory path to list")


class OpenAppRequest(BaseModel):
    target: str = Field(..., description="App name, file, folder, or URL to open")


@router.post("/files/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload one or more files from the user to the symbiote.
    Extracts text previews from code and document files.
    """
    saved_files = []
    text_extensions = {
        ".txt", ".md", ".py", ".ts", ".tsx", ".js", ".jsx",
        ".json", ".yaml", ".yml", ".html", ".css", ".csv",
        ".sh", ".bat", ".sql", ".env", ".toml", ".xml",
    }

    for file in files:
        if not file.filename:
            continue

        clean_filename = Path(file.filename).name
        dest_path = UPLOAD_DIR / clean_filename

        content_bytes = await file.read()
        dest_path.write_bytes(content_bytes)

        # Attempt text preview for text/code files
        ext = dest_path.suffix.lower()
        text_preview = ""
        is_text = ext in text_extensions

        if is_text:
            try:
                decoded = content_bytes.decode("utf-8", errors="replace")
                text_preview = decoded[:3000]
            except Exception:
                is_text = False

        saved_files.append({
            "filename": clean_filename,
            "path": str(dest_path.resolve()),
            "size_bytes": len(content_bytes),
            "is_text": is_text,
            "preview": text_preview,
        })

    return {
        "status": "success",
        "message": f"Successfully ingested {len(saved_files)} file(s).",
        "files": saved_files,
    }


@router.post("/system/command")
async def run_command(payload: CommandRequest):
    """Execute a shell or PowerShell command on the host machine."""
    result = execute_terminal_command(payload.command, timeout=payload.timeout)
    return result


@router.get("/system/vitals")
async def get_vitals():
    """Retrieve host machine vitals (OS, disk, architecture, user)."""
    return system_vitals()


@router.post("/system/read-file")
async def api_read_file(payload: FileReadRequest):
    """Read a file from the host machine."""
    result = read_file(payload.path, max_chars=payload.max_chars)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to read file"))
    return result


@router.post("/system/write-file")
async def api_write_file(payload: FileWriteRequest):
    """Write or update a file on the host machine."""
    result = write_file(payload.path, payload.content)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to write file"))
    return result


@router.post("/system/list-dir")
async def api_list_dir(payload: ListDirRequest):
    """List entries inside a directory on the host machine."""
    result = list_directory(payload.path)
    return result


@router.post("/system/open")
async def api_open_app(payload: OpenAppRequest):
    """Launch an application or open a file/folder in Explorer."""
    return open_application(payload.target)
