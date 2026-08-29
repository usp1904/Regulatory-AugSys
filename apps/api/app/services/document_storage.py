"""MIME validation and filesystem persistence for controlled documents."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings

EXTENSION_BY_MIME = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
}

MIME_BY_EXTENSION = {value: key for key, value in EXTENSION_BY_MIME.items()}


class DocumentValidationError(ValueError):
    """Raised when upload metadata or size is invalid."""


@dataclass(frozen=True)
class StoredUpload:
    filename: str
    content_type: str
    byte_size: int
    file_hash: str
    storage_path: str


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


def normalize_content_type(content_type: str | None) -> str:
    return (content_type or "application/octet-stream").split(";")[0].strip().lower()


def validate_upload_metadata(filename: str, content_type: str | None, byte_size: int) -> str:
    settings = get_settings()
    if byte_size > settings.max_upload_bytes:
        raise DocumentValidationError(
            f"File exceeds maximum size of {settings.max_upload_bytes} bytes"
        )

    media_type = normalize_content_type(content_type)
    if media_type not in settings.allowed_mime_set:
        raise DocumentValidationError(f"Unsupported media type: {media_type}")

    ext = Path(filename).suffix.lower()
    expected_ext = EXTENSION_BY_MIME.get(media_type)
    if expected_ext and ext != expected_ext:
        raise DocumentValidationError(
            f"Filename extension {ext!r} does not match media type {media_type!r}"
        )

    return media_type


async def read_upload_bytes(file: UploadFile) -> bytes:
    data = await file.read()
    validate_upload_metadata(file.filename or "upload.bin", file.content_type, len(data))
    return data


def persist_original_bytes(filename: str, data: bytes, content_type: str) -> StoredUpload:
    file_hash = sha256_bytes(data)
    safe_name = safe_filename(filename)
    root = ensure_storage_root()
    version_dir = root / file_hash[:2]
    version_dir.mkdir(parents=True, exist_ok=True)
    dest = version_dir / f"{file_hash}_{safe_name}"
    if not dest.exists():
        dest.write_bytes(data)

    return StoredUpload(
        filename=safe_name,
        content_type=content_type,
        byte_size=len(data),
        file_hash=file_hash,
        storage_path=str(dest),
    )


def audit_detail(**kwargs: object) -> str:
    return json.dumps(kwargs, default=str)
