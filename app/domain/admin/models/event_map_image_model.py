from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.admin_db import AdminBase

class EventMapImage(AdminBase):
    __tablename__ = "event_map_images"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(500), nullable=False)
    image_order = Column(Integer, default=0)  # Ordem das imagens (0, 1, 2, 3, 4) - máximo 5
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="map_images")

