# app/domain/admin/models/product_event_image_model.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.admin_db import AdminBase

class ProductEventImage(AdminBase):
    __tablename__ = "product_event_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products_event.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(500), nullable=False)
    image_order = Column(Integer, default=0)  # Ordem das imagens (0, 1, 2, ...)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("ProductEvent", back_populates="images")

