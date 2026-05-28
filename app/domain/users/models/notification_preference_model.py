from sqlalchemy import Column, Integer, Boolean, DateTime, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.config.notification_db import NotificationBase

class NotificationPreference(NotificationBase):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Tipos de notificações (padrão: True = habilitado)
    lineup_updated = Column(Boolean, default=True, nullable=False)
    news_feed = Column(Boolean, default=True, nullable=False)  # Posts lançados
    interactions = Column(Boolean, default=True, nullable=False)  # Curtir/comentar comentário
    new_events = Column(Boolean, default=True, nullable=False)  # Novos eventos disponíveis
    push_enabled = Column(Boolean, default=False, nullable=False)  # Notificações no navegador (Web Push)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_notification_preferences_user"),
        Index("idx_notification_preferences_user", "user_id"),
    )

