# Comment Model (para armazenar os comentários nas notícias)
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.config.interaction_db import InteractionBase

class Comment(InteractionBase):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    news_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    event_id = Column(Integer, nullable=True, index=True)
    parent_comment_id = Column(Integer, ForeignKey('comments.id'), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_user_id = Column(Integer, nullable=True)

    __table_args__ = (
        # Índice em news_id para consultas frequentes por notícia
        Index("idx_comments_news_id", "news_id"),
        # Índice em parent_comment_id para buscar respostas
        Index("idx_comments_parent_id", "parent_comment_id"),
        # Índice composto para consultas com filtro de deleted_at
        Index("idx_comments_news_deleted", "news_id", "deleted_at"),
        # Índice em event_id para consultas por evento
        Index("idx_comments_event_id", "event_id"),
    )


