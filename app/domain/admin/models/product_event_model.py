# app/domain/admin/models/product_event_model.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.admin_db import AdminBase

class ProductEvent(AdminBase):
    __tablename__ = "products_event"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)  # Preço com 2 casas decimais
    status = Column(String(20), default="active")  # "active", "inactive", "deleted"
    stock = Column(Integer, default=0, nullable=False)  # Estoque
    last_pieces = Column(Boolean, default=False, nullable=False)  # Últimas peças
    
    # Relacionamento com evento (obrigatório)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    
    # Auditoria
    created_by_id = Column(Integer, nullable=False)  # ID do usuário que criou
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_id = Column(Integer, nullable=True)  # ID do usuário que atualizou
    
    # Sistema de soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_id = Column(Integer, nullable=True)  # ID do usuário que deletou
    
    # Relacionamentos
    event = relationship("Event", backref="products")
    images = relationship("ProductEventImage", back_populates="product", cascade="all, delete-orphan", order_by="ProductEventImage.image_order")

