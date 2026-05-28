from sqlalchemy import Column, Integer, Boolean, String, DateTime, Index
from sqlalchemy.sql import func
from app.config.interaction_db import InteractionBase

class Like(InteractionBase):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    event_id = Column(Integer, nullable=True, index=True)
    
    # Campos de histórico e auditoria
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 ou IPv6
    user_agent = Column(String(1000), nullable=True)  # User Agent do dispositivo
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Índice composto para consultas (user_id, news_id, is_active)
        # A verificação de unicidade para likes ativos será feita no código
        Index("idx_likes_user_news_active", "user_id", "news_id", "is_active"),
        # Índice composto para consultas (user_id, news_id)
        Index("idx_likes_user_news", "user_id", "news_id"),
        # Índice individual em news_id para contagens e agregações
        Index("idx_likes_news_id", "news_id"),
        # Índice individual em user_id para buscar todos os likes de um usuário
        Index("idx_likes_user_id", "user_id"),
        # Índice para histórico (buscar por is_active)
        Index("idx_likes_is_active", "is_active"),
        # Índice em event_id para consultas por evento
        Index("idx_likes_event_id", "event_id"),
    )
