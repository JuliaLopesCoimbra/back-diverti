from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.sql import func
from app.config.notification_db import NotificationBase

class Notification(NotificationBase):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Usuário que recebe a notificação
    type = Column(String(50), nullable=False, index=True)  # Tipo: comment_reply, comment_like, post_like, post_approved, post_approved_admin, post_rejected, post_deactivated, new_post, lineup_updated, new_event
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Referências opcionais para entidades relacionadas
    related_user_id = Column(Integer, nullable=True)  # Quem fez a ação (ex: quem comentou) - último usuário quando agrupado
    related_news_id = Column(Integer, nullable=True)  # Post relacionado
    related_comment_id = Column(Integer, nullable=True)  # Comentário relacionado
    related_event_id = Column(Integer, nullable=True)  # Evento relacionado
    broadcast_sender_id = Column(Integer, nullable=True)  # Quem enviou a notificação de broadcast (admin/admin_master)
    
    # Campos para agrupamento de notificações
    count = Column(Integer, default=1, nullable=False)  # Quantidade de pessoas que fizeram a ação (para agrupamento)
    
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_notifications_user_unread", "user_id", "is_read", "created_at"),
        Index("idx_notifications_user_created", "user_id", "created_at"),
    )

