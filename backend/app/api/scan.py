"""Image upload endpoint for LegalMetriX label scanning."""

import asyncio
import logging
import os
import secrets
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from google.genai import errors
from PIL import Image, UnidentifiedImageError

from app.schemas import LabelAnalysis, ScanResponse
from app.services.gemini_service import LabelAnalysisError, analyze_label

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per uploaded image
READ_CHUNK = 64 * 1024

# Maps PIL image formats back to a file extension used for storage.
_FORMAT_EXT = {
    "jpeg": "jpg",
    "png": "png",
    "webp": "webp",
    "gif": "gif",
    "bmp": "bmp",
    "tiff": "tiff",
}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Reject requests that do not carry the configured X-API-Key.

    Each request behind this endpoint spends Gemini inference credits, so the
    endpoint must not be publicly open. The key is compared in constant time,
    and requests are refused entirely if the server has no key configured
    (rather than silently running open).
    """
    expected = os.getenv("LEGALMETRIX_API_KEY") or ""
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Server authentication is not configured",
        )
    if not secrets.compare_digest(x_api_key or "", expected):
        raise HTTPException(
            status_code=401, detail="Invalid or missing X-API-Key header"
        )


async def _read_limited(file: UploadFile, limit: int) -> bytes:
    """Stream the upload into memory, aborting with 413 past the size limit."""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(READ_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {limit // (1024 * 1024)} MB)",
            )
        chunks.append(chunk)
    if total == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    return b"".join(chunks)


def _verify_image(data: bytes) -> str:
    """Confirm the upload is a decodable image and return its PIL format."""
    try:
        with Image.open(BytesIO(data)) as probe:
            probe.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image",
        ) from exc
    with Image.open(BytesIO(data)) as probe:
        fmt = (probe.format or "").lower()
    return fmt


@router.post("/upload", response_model=ScanResponse)
async def upload_image(
    file: UploadFile = File(...),
    _: None = Depends(require_api_key),
):
    """Analyze a packaged-commodity label image and return compliance fields."""
    data = await _read_limited(file, MAX_FILE_SIZE)

    try:
        fmt = _verify_image(data)
    except HTTPException:
        raise

    ext = _FORMAT_EXT.get(fmt, "img")
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = UPLOAD_DIR / filename
    file_path.write_bytes(data)

    try:
        analysis = await asyncio.to_thread(analyze_label, str(file_path))
    except LabelAnalysisError as exc:
        logger.warning("Label analysis failed for %s: %s", file_path.name, exc)
        raise HTTPException(
            status_code=502, detail="Label analysis failed"
        ) from exc
    except errors.APIError as exc:
        logger.warning("Gemini API error while analyzing %s: %s", file_path.name, exc)
        raise HTTPException(
            status_code=502, detail="Label analysis service error"
        ) from exc
    except Exception:
        logger.exception("Unexpected error while analyzing %s", file_path.name)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        # This is a stateless API; the temp image is not needed after the
        # analysis completes (success or failure).
        file_path.unlink(missing_ok=True)

    return ScanResponse(
        success=True,
        filename=file.filename or filename,
        analysis=LabelAnalysis.model_validate(analysis),
    )