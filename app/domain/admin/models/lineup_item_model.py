# app/domain/admin/models/lineup_item_model.py

from sqlalchemy import Column, Integer, String, ForeignKey, Time, DateTime, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.admin_db import AdminBase

class LineupItem(AdminBase):
    __tablename__ = "lineup_items"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    artist_name = Column(String(255), nullable=False)
    artist_image_url = Column(String(500), nullable=True)
    performance_time = Column(Time, nullable=False)
    performance_end_time = Column(Time, nullable=True)  # Horário de término da apresentação
    stage = Column(String(100), nullable=True)  # Palco onde o artista irá apresentar
    event_date = Column(Date, nullable=True)  # Data do evento em que o artista irá apresentar
    display_order = Column(Integer, default=0)  # Ordem de exibição (0, 1, 2, ...)
    description = Column(Text, nullable=True)  # Descrição do artista
    
    # Auditoria
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_id = Column(Integer, nullable=True)  # ID do usuário que criou
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by_id = Column(Integer, nullable=True)  # ID do usuário que atualizou
    
    # Sistema de soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_id = Column(Integer, nullable=True)  # ID do usuário que deletou

    event = relationship("Event", backref="lineup_items")

