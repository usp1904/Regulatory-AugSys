"""Local file storage for in-house documents."""

import hashlib
import re
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings

TEXT_EXTENSIONS = {".txt", ".csv", ".json"}
MAX_BYTES = 5 * 1024 * 1024


def ensure_storage_root() -> Path:
    root = Path(get_settings().storage_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_filename(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    return cleaned or "upload.bin"


def extract_text(filename: str, data: bytes) -> tuple[str, str]:
    ext = Path(filename).suffix.lower()
    if ext not in TEXT_EXTENSIONS:
        return "UNSUPPORTED_BINARY", ""
    try:
        text = data.decode("utf-8", errors="replace")
    except OSError:
        return "PARSE_ERROR", ""
    return "PARSED", text[:8000]


async def save_upload(file: UploadFile) -> tuple[str, str, str, str, int]:
    """Persist upload and return filename, hash, storage path, parse status, size."""
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise ValueError("File exceeds 5 MB limit")

    file_hash = sha256_bytes(data)
    filename = safe_filename(file.filename or "upload.bin")
    root = ensure_storage_root()
    dest = root / f"{file_hash[:16]}_{filename}"
    dest.write_bytes(data)

    parse_status, excerpt = extract_text(filename, data)
    return filename, file_hash, str(dest), parse_status, len(data)
