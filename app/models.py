from sqlalchemy import Column, String, Integer, DateTime, Enum, JSON, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.sqlite import BLOB
from app.database import Base
import enum

class StatusEnum(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"

class Image(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True)
    original_name = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    ext = Column(String, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.queued, nullable=False)

    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    format = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)

    exif = Column(JSON, nullable=True)
    caption = Column(Text, nullable=True)

    original_path = Column(String, nullable=False)
    thumb_small_path = Column(String, nullable=True)
    thumb_medium_path = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    processing_ms = Column(Float, nullable=True)
    error = Column(Text, nullable=True)
