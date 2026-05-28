from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from app.config.interaction_db import InteractionBase

class DownloadedPhoto(InteractionBase):
    __tablename__ = "downloaded_photos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    image_url = Column(String(500), nullable=False)
    event_id = Column(Integer, nullable=True, index=True)
    event_name = Column(String(255), nullable=True)
    similarity = Column(String(50), nullable=True)  # Similaridade da busca por IA
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("idx_downloaded_photos_user_id", "user_id"),
        Index("idx_downloaded_photos_event_id", "event_id"),
        Index("idx_downloaded_photos_downloaded_at", "downloaded_at"),
        Index("idx_downloaded_photos_user_downloaded", "user_id", "downloaded_at"),
    )




