import os, uuid, threading, queue
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.database import Base, engine, get_db
from app.models import Image as ImageModel, StatusEnum
from app.schemas import ImageOut, ListImageOut, StatsOut, ThumbnailURLs
from app.processing import validate_upload, secure_ext, ORIGINALS_DIR, process_image

# Ensure DB tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

# CORS (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-process job queue + worker thread
job_q: "queue.Queue[str]" = queue.Queue()

def worker():
    from app.database import SessionLocal  # local to avoid circular import with get_db
    db = SessionLocal()
    logger.info("Background worker started.")
    try:
        while True:
            record_id = job_q.get()
            if record_id is None:
                break
            from app.processing import process_image
            process_image(db, record_id)
            job_q.task_done()
    finally:
        db.close()

t = threading.Thread(target=worker, daemon=True)
t.start()

def build_thumb_urls(image_id: str) -> ThumbnailURLs:
    base = settings.BASE_URL.rstrip("/")
    return ThumbnailURLs(
        small=f"{base}/api/images/{image_id}/thumbnails/small",
        medium=f"{base}/api/images/{image_id}/thumbnails/medium",
    )

@app.post("/api/images", response_model=Dict[str, Any], status_code=202, tags=["images"])
def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validate file type
    ok, msg = validate_upload(file.filename, file.content_type or "")
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # Check file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file_content = file.file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is 10MB.")
    file.file.seek(0)  # Reset file pointer

    image_id = str(uuid.uuid4())
    ext = secure_ext(file.filename)
    os.makedirs(ORIGINALS_DIR, exist_ok=True)
    save_path = os.path.join(ORIGINALS_DIR, f"{image_id}{ext}")

    # Save original (using the content we already read)
    with open(save_path, "wb") as f:
        f.write(file_content)

    rec = ImageModel(
        id=image_id,
        original_name=file.filename,
        content_type=file.content_type or "",
        ext=ext,
        status=StatusEnum.queued,
        original_path=save_path,
    )
    db.add(rec)
    db.commit()

    # Enqueue background processing
    job_q.put(image_id)

    data = {
        "image_id": image_id,
        "original_name": file.filename,
        "status": rec.status.value,
        "thumbnails": build_thumb_urls(image_id).model_dump(),
    }
    return {"status": "accepted", "data": data, "error": None}

@app.get("/api/images", response_model=List[ListImageOut], tags=["images"]) 
def list_images(db: Session = Depends(get_db)):
    q = db.query(ImageModel).order_by(ImageModel.created_at.desc()).all()
    return [
        ListImageOut(
            id=i.id, original_name=i.original_name, status=i.status.value,
            created_at=i.created_at, processed_at=i.processed_at
        ) for i in q
    ]

@app.get("/api/images/{image_id}", response_model=ImageOut, tags=["images"]) 
def get_image(image_id: str, db: Session = Depends(get_db)):
    rec = db.get(ImageModel, image_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Image not found")
    meta = {
        "width": rec.width,
        "height": rec.height,
        "format": rec.format,
        "size_bytes": rec.size_bytes,
        "exif": rec.exif,
    }
    return ImageOut(
        id=rec.id,
        original_name=rec.original_name,
        processed_at=rec.processed_at,
        status=rec.status.value,
        metadata=meta,
        thumbnails=build_thumb_urls(rec.id),
        caption=rec.caption,
        error=rec.error,
    )

@app.get("/api/images/{image_id}/thumbnails/{size}", tags=["images"]) 
def get_thumbnail(image_id: str, size: str, db: Session = Depends(get_db)):
    rec = db.get(ImageModel, image_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Image not found")

    if size == "small":
        path = rec.thumb_small_path
    elif size == "medium":
        path = rec.thumb_medium_path
    else:
        raise HTTPException(status_code=400, detail="size must be 'small' or 'medium'")

    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Thumbnail not available yet")
    return FileResponse(path, media_type="image/jpeg", filename=f"{image_id}_{size}.jpg")

@app.get("/api/stats", response_model=StatsOut, tags=["stats"]) 
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(ImageModel.id)).scalar() or 0
    done = db.query(func.count(ImageModel.id)).filter(ImageModel.status == StatusEnum.done).scalar() or 0
    failed = db.query(func.count(ImageModel.id)).filter(ImageModel.status == StatusEnum.failed).scalar() or 0
    processing = db.query(func.count(ImageModel.id)).filter(ImageModel.status == StatusEnum.processing).scalar() or 0
    queued = db.query(func.count(ImageModel.id)).filter(ImageModel.status == StatusEnum.queued).scalar() or 0
    avg_ms = db.query(func.avg(ImageModel.processing_ms)).filter(ImageModel.processing_ms.isnot(None)).scalar()

    success_rate = (done / total * 100.0) if total > 0 else 0.0
    return StatsOut(
        total=total, done=done, failed=failed, processing=processing, queued=queued,
        success_rate=round(success_rate, 2),
        average_processing_ms=float(avg_ms) if avg_ms is not None else None,
    )

@app.get("/") 
def root():
    return {"message": f"{settings.APP_NAME} is running."}
