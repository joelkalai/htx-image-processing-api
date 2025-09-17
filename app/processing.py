import os, uuid, time
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any
from PIL import Image as PILImage, ExifTags
from sqlalchemy.orm import Session
from loguru import logger

from app.models import Image as ImageModel, StatusEnum
from app.config import settings
from app.caption import caption_image

ORIGINALS_DIR = os.path.join("storage", "originals")
SMALL_DIR = os.path.join("storage", "thumbs", "small")
MEDIUM_DIR = os.path.join("storage", "thumbs", "medium")

ALLOWED_EXTS = {".jpg", ".jpeg", ".png"}
ALLOWED_CT = {"image/jpeg", "image/jpg", "image/png"}

SMALL_SIZE = 256
MEDIUM_SIZE = 768

def secure_ext(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".jpeg":
        ext = ".jpg"
    return ext

def validate_upload(filename: str, content_type: str) -> Tuple[bool, str]:
    ext = secure_ext(filename)
    if ext not in ALLOWED_EXTS:
        return False, f"Unsupported file extension: {ext}. Only JPG and PNG are supported."
    if content_type.lower() not in ALLOWED_CT:
        return False, f"Unsupported content-type: {content_type}. Only image/jpeg and image/png are supported."
    return True, ""

def extract_exif(pil_img: PILImage.Image) -> Optional[Dict[str, Any]]:
    try:
        exif_data = pil_img._getexif()
        if not exif_data:
            return None
        decoded = {}
        for tag, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag, tag)
            # Many EXIF values are not JSON-serializable; stringify conservatively
            try:
                decoded[tag_name] = value if isinstance(value, (int, float, str)) else str(value)
            except Exception:
                decoded[tag_name] = str(value)
        return decoded
    except Exception:
        return None

def gen_thumb(src_path: str, dst_path: str, max_size: int) -> Tuple[int, int]:
    with PILImage.open(src_path) as img:
        img = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
        img.thumbnail((max_size, max_size))
        # Ensure parent dir exists
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        img.save(dst_path, format="JPEG", quality=90)
        return img.width, img.height

def process_image(db: Session, record_id: str) -> None:
    rec = db.get(ImageModel, record_id)
    if not rec:
        logger.error(f"Record {record_id} not found in DB for processing")
        return
    if rec.status in (StatusEnum.done, StatusEnum.processing):
        return

    rec.status = StatusEnum.processing
    db.commit()

    start_ns = time.time_ns()
    try:
        # Extract metadata
        with PILImage.open(rec.original_path) as pil:
            width, height = pil.width, pil.height
            fmt = pil.format or rec.ext.lstrip(".")
            # File size
            size_bytes = os.path.getsize(rec.original_path)
            exif = extract_exif(pil)

        # Generate thumbnails
        small_path = os.path.join(SMALL_DIR, f"{rec.id}.jpg")
        medium_path = os.path.join(MEDIUM_DIR, f"{rec.id}.jpg")
        gen_thumb(rec.original_path, small_path, SMALL_SIZE)
        gen_thumb(rec.original_path, medium_path, MEDIUM_SIZE)

        # Optional caption
        caption = caption_image(rec.original_path)

        # Update record
        rec.width = width
        rec.height = height
        rec.format = (fmt or "").lower()
        rec.size_bytes = size_bytes
        rec.exif = exif
        rec.caption = caption
        rec.thumb_small_path = small_path
        rec.thumb_medium_path = medium_path
        rec.status = StatusEnum.done
        rec.processed_at = datetime.now(timezone.utc)

        elapsed_ms = (time.time_ns() - start_ns) / 1e6
        rec.processing_ms = elapsed_ms
        rec.error = None

        db.commit()
        logger.info(f"Processed {rec.id} in {elapsed_ms:.1f} ms")
    except Exception as e:
        rec.status = StatusEnum.failed
        rec.error = str(e)
        rec.processed_at = datetime.now(timezone.utc)
        elapsed_ms = (time.time_ns() - start_ns) / 1e6
        rec.processing_ms = elapsed_ms
        db.commit()
        logger.exception(f"Failed processing {rec.id}: {e}")

