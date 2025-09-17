from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime

class ThumbnailURLs(BaseModel):
    small: Optional[str] = None
    medium: Optional[str] = None

class ImageOut(BaseModel):
    image_id: str = Field(..., alias="id")
    original_name: str
    processed_at: Optional[datetime] = None
    status: str
    metadata: Dict[str, Any]
    thumbnails: ThumbnailURLs
    caption: Optional[str] = None
    error: Optional[str] = None

    class Config:
        populate_by_name = True

class ListImageOut(BaseModel):
    id: str
    original_name: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None

class StatsOut(BaseModel):
    total: int
    done: int
    failed: int
    processing: int
    queued: int
    success_rate: float
    average_processing_ms: Optional[float] = None
