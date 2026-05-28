from sqlalchemy import Column, Integer, Boolean, String, DateTime, Index
from sqlalchemy.sql import func
from app.config.interaction_db import InteractionBase

class CommentLike(InteractionBase):
    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    event_id = Column(Integer, nullable=True, index=True)
    
    # Campos de histórico e auditoria
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 ou IPv6
    user_agent = Column(String(1000), nullable=True)  # User Agent do dispositivo
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Índice composto para consultas (user_id, comment_id, is_active)
        # A verificação de unicidade para likes ativos será feita no código
        Index("idx_comment_likes_user_comment_active", "user_id", "comment_id", "is_active"),
        # Índice composto para consultas frequentes (user_id, comment_id)
        Index("idx_comment_likes_user_comment", "user_id", "comment_id"),
        # Índice individual em comment_id para contagens
        Index("idx_comment_likes_comment_id", "comment_id"),
        # Índice para histórico (buscar por is_active)
        Index("idx_comment_likes_is_active", "is_active"),
        # Índice em event_id para consultas por evento
        Index("idx_comment_likes_event_id", "event_id"),
    )

