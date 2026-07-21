"""
AutoWorth AI — Image Service

Handles all image I/O operations:
  - Validating uploaded files (MIME type, resolution, size, aspect ratio)
  - Uploading raw vehicle images to Cloudinary
  - Uploading generated damage heatmaps to Cloudinary
  - Deleting images from Cloudinary
  - Selecting the best image angle for primary CV processing

Cloudinary folder layout:
  {prefix}/raw/{prediction_id}/{angle}_{uuid}.jpg
  {prefix}/heatmaps/{prediction_id}/heatmap_{uuid}.jpg

Layer: Service Layer
"""

from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path
from typing import Any

import cloudinary
import cloudinary.uploader
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings
from app.models.prediction_image import ImageAngle

logger = logging.getLogger(__name__)

settings = get_settings()

# ── Cloudinary SDK Configuration ──────────────────────────────────────────────
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

# ── Validation Constants ───────────────────────────────────────────────────────
ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/jpg", "image/png", "image/webp"}
)
MIN_RESOLUTION_PX: int = 300          # Minimum dimension in either axis
MAX_FILE_SIZE_BYTES: int = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
ASPECT_RATIO_MIN: float = 0.5         # Narrowest accepted portrait ratio
ASPECT_RATIO_MAX: float = 3.0         # Widest accepted landscape ratio

# Priority order for primary image selection (index 0 = highest priority)
_PRIMARY_ANGLE_PRIORITY: list[ImageAngle] = [
    ImageAngle.FRONT,
    ImageAngle.LEFT,
    ImageAngle.RIGHT,
    ImageAngle.REAR,
    ImageAngle.INTERIOR,
    ImageAngle.OTHER,
]


class ImageValidationError(Exception):
    """Raised when an uploaded image fails validation checks."""


class ImageUploadError(Exception):
    """Raised when a Cloudinary upload operation fails."""


# ── Validation ─────────────────────────────────────────────────────────────────
def validate_image(
    file_bytes: bytes,
    content_type: str,
    filename: str = "upload",
) -> dict[str, Any]:
    """
    Validate an uploaded image file.

    Checks:
    - MIME type is JPEG, PNG, or WebP
    - File size does not exceed MAX_UPLOAD_SIZE_MB
    - Image is decodable (not corrupt)
    - Both dimensions ≥ MIN_RESOLUTION_PX
    - Aspect ratio between ASPECT_RATIO_MIN and ASPECT_RATIO_MAX

    Returns:
        dict with keys: width, height, format, size_bytes, aspect_ratio

    Raises:
        ImageValidationError on any failed check.
    """
    # ── MIME type ─────────────────────────────────────────────
    normalised_mime = content_type.lower().strip()
    if normalised_mime not in ALLOWED_MIME_TYPES:
        raise ImageValidationError(
            f"Unsupported file type '{content_type}'. "
            f"Accepted types: JPEG, PNG, WebP."
        )

    # ── File size ─────────────────────────────────────────────
    size_bytes = len(file_bytes)
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise ImageValidationError(
            f"File '{filename}' exceeds the maximum allowed size of "
            f"{settings.MAX_UPLOAD_SIZE_MB} MB "
            f"(received {size_bytes / 1_048_576:.1f} MB)."
        )

    # ── Decodability & resolution ─────────────────────────────
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            width, height = img.size
            fmt = img.format or "UNKNOWN"
    except (UnidentifiedImageError, Exception) as exc:
        raise ImageValidationError(
            f"File '{filename}' could not be decoded as a valid image: {exc}"
        ) from exc

    if width < MIN_RESOLUTION_PX or height < MIN_RESOLUTION_PX:
        raise ImageValidationError(
            f"Image '{filename}' resolution {width}×{height} is too small. "
            f"Minimum required: {MIN_RESOLUTION_PX}×{MIN_RESOLUTION_PX} px."
        )

    # ── Aspect ratio ──────────────────────────────────────────
    aspect_ratio = width / height
    if not (ASPECT_RATIO_MIN <= aspect_ratio <= ASPECT_RATIO_MAX):
        raise ImageValidationError(
            f"Image '{filename}' aspect ratio {aspect_ratio:.2f} is out of range "
            f"[{ASPECT_RATIO_MIN}, {ASPECT_RATIO_MAX}]. "
            "Please upload a standard landscape or portrait vehicle photo."
        )

    logger.debug(
        "✅ [ImageService] Validated '%s' — %dx%d px, %.2f AR, %.1f KB",
        filename,
        width,
        height,
        aspect_ratio,
        size_bytes / 1024,
    )

    return {
        "width": width,
        "height": height,
        "format": fmt,
        "size_bytes": size_bytes,
        "aspect_ratio": round(aspect_ratio, 3),
    }


# ── Cloudinary Upload ──────────────────────────────────────────────────────────
def upload_raw_image(
    file_bytes: bytes,
    prediction_id: uuid.UUID,
    angle: ImageAngle,
    filename: str = "image",
) -> dict[str, str]:
    """
    Upload a raw vehicle image to Cloudinary.

    Cloudinary path: {prefix}/raw/{prediction_id}/{angle}_{unique_id}

    Returns:
        dict with keys: url (secure_url), public_id
    """
    _ensure_cloudinary_configured()

    folder = f"{settings.CLOUDINARY_FOLDER_PREFIX}/raw/{prediction_id}"
    public_id = f"{folder}/{angle.value.replace(' ', '_').lower()}_{uuid.uuid4().hex[:8]}"

    try:
        result = cloudinary.uploader.upload(
            file_bytes,
            public_id=public_id,
            overwrite=False,
            resource_type="image",
            format="jpg",
            quality="auto:good",
            fetch_format="auto",
            tags=["autoworth", "raw", str(prediction_id)],
        )
        logger.info(
            "☁️  [ImageService] Uploaded raw image — public_id=%s", result["public_id"]
        )
        return {"url": result["secure_url"], "public_id": result["public_id"]}
    except Exception as exc:
        logger.error("❌ [ImageService] Raw upload failed: %s", exc)
        raise ImageUploadError(f"Cloudinary upload failed: {exc}") from exc


def upload_heatmap(
    heatmap_bytes: bytes,
    prediction_id: uuid.UUID,
) -> dict[str, str]:
    """
    Upload a damage heatmap PNG to Cloudinary.

    Cloudinary path: {prefix}/heatmaps/{prediction_id}/heatmap_{unique_id}

    Returns:
        dict with keys: url (secure_url), public_id
    """
    _ensure_cloudinary_configured()

    folder = f"{settings.CLOUDINARY_FOLDER_PREFIX}/heatmaps/{prediction_id}"
    public_id = f"{folder}/heatmap_{uuid.uuid4().hex[:8]}"

    try:
        result = cloudinary.uploader.upload(
            heatmap_bytes,
            public_id=public_id,
            overwrite=False,
            resource_type="image",
            format="png",
            tags=["autoworth", "heatmap", str(prediction_id)],
        )
        logger.info(
            "☁️  [ImageService] Uploaded heatmap — public_id=%s", result["public_id"]
        )
        return {"url": result["secure_url"], "public_id": result["public_id"]}
    except Exception as exc:
        logger.error("❌ [ImageService] Heatmap upload failed: %s", exc)
        raise ImageUploadError(f"Cloudinary heatmap upload failed: {exc}") from exc


def delete_image(public_id: str) -> bool:
    """
    Delete an image from Cloudinary by its public_id.

    Returns:
        True on success, False if the image was not found or deletion failed.
    """
    _ensure_cloudinary_configured()
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="image")
        success = result.get("result") == "ok"
        if success:
            logger.info("🗑️  [ImageService] Deleted image — public_id=%s", public_id)
        return success
    except Exception as exc:
        logger.warning("⚠️  [ImageService] Delete failed for %s: %s", public_id, exc)
        return False


# ── Primary Image Selection ────────────────────────────────────────────────────
def select_primary_angle(available_angles: list[ImageAngle]) -> ImageAngle | None:
    """
    Select the best image angle for primary CV damage processing.

    Priority: Front > Left Side > Right Side > Rear > Interior > Other

    Returns:
        The preferred ImageAngle enum value, or None if no angles are available.
    """
    for preferred in _PRIMARY_ANGLE_PRIORITY:
        if preferred in available_angles:
            return preferred
    return available_angles[0] if available_angles else None


# ── Internal Helpers ───────────────────────────────────────────────────────────
def _ensure_cloudinary_configured() -> None:
    """Raise if Cloudinary credentials are missing (fail fast, clear message)."""
    if not settings.CLOUDINARY_CLOUD_NAME:
        raise ImageUploadError(
            "Cloudinary is not configured. "
            "Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET "
            "in your environment variables."
        )
