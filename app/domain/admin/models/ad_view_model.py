# app/domain/admin/models/ad_view_model.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.admin_db import AdminBase

class AdView(AdminBase):
    __tablename__ = "ad_views"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Referência ao users do auth_db (sem FK pois está em outro banco)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    ad_identifier = Column(String(255), nullable=False, index=True)  # Identificador do anúncio
    ad_url = Column(Text, nullable=True)  # URL do anúncio visualizado
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relacionamento com evento
    event = relationship("Event", backref="ad_views")
    
    __table_args__ = (
        Index("idx_ad_views_user_id", "user_id"),
        Index("idx_ad_views_event_id", "event_id"),
        Index("idx_ad_views_viewed_at", "viewed_at"),
        Index("idx_ad_views_ad_identifier", "ad_identifier"),
        # Índices compostos para queries de estatísticas
        Index("idx_ad_views_event_ad", "event_id", "ad_identifier", "viewed_at"),
    )




