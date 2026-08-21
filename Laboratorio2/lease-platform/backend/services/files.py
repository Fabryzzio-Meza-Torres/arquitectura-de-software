from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import HTTPException, UploadFile


MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_CREDIT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "data" / "uploads"


async def inspect_upload(file: UploadFile, *, pdf_only: bool = False) -> tuple[bytes, str]:
    data = await file.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds the 20 MB limit")
    allowed = {"application/pdf"} if pdf_only else ALLOWED_CREDIT_TYPES
    if file.content_type not in allowed:
        raise HTTPException(status_code=422, detail=f"Unsupported content type: {file.content_type}")
    if not data:
        raise HTTPException(status_code=422, detail="Empty file")
    digest = hashlib.sha256(data).hexdigest()
    return data, digest


def contains_eicar(data: bytes) -> bool:
    return b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in data


def persist_upload(data: bytes, digest: str, original_name: str) -> str:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(original_name).suffix.lower()[:10]
    stored_name = f"{digest}{suffix}"
    target = UPLOAD_DIR / stored_name
    if not target.exists():
        target.write_bytes(data)
    return stored_name

