# app/domain/admin/models/ad_click_model.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.admin_db import AdminBase

class AdClick(AdminBase):
    __tablename__ = "ad_clicks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Referência ao users do auth_db (sem FK pois está em outro banco)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    ad_identifier = Column(String(255), nullable=False, index=True)  # Identificador do anúncio (ex: "1", "2", "adplugg_123")
    ad_url = Column(Text, nullable=True)  # URL do anúncio clicado
    redirect_url = Column(Text, nullable=True)  # URL de redirecionamento
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relacionamento com evento
    event = relationship("Event", backref="ad_clicks")
    
    __table_args__ = (
        Index("idx_ad_clicks_user_id", "user_id"),
        Index("idx_ad_clicks_event_id", "event_id"),
        Index("idx_ad_clicks_clicked_at", "clicked_at"),
        Index("idx_ad_clicks_ad_identifier", "ad_identifier"),
    )




