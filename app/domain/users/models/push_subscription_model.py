from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.sql import func
from app.config.notification_db import NotificationBase


class PushSubscription(NotificationBase):
    """Assinatura Web Push do usuário (um usuário pode ter vários dispositivos)."""
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    endpoint = Column(String(1024), nullable=False, unique=True)  # URL única do push service
    p256dh = Column(Text, nullable=False)   # Chave pública do cliente (encoding base64)
    auth = Column(Text, nullable=False)    # Secret de autenticação (encoding base64)
    user_agent = Column(String(512), nullable=True)  # Opcional: identificar dispositivo
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_push_subscriptions_user", "user_id"),
    )
