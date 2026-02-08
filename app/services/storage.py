import os
from uuid import uuid4
from fastapi import UploadFile
from pathlib import Path
from typing import Tuple

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "./storage/docs")
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def save_upload_file(upload_file: UploadFile) -> Tuple[str, str, int]:
    """Save UploadFile to disk. Returns (filename, filepath, size)."""
    ext = Path(upload_file.filename).suffix
    safe_name = f"{uuid4().hex}{ext}"
    dest = Path(UPLOAD_DIR) / safe_name
    with dest.open("wb") as f:
        content = upload_file.file.read()
        f.write(content)
    size = dest.stat().st_size
    return (upload_file.filename, str(dest), size)


def get_file_path(filepath: str) -> str:
    return filepath

