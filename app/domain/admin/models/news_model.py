from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.admin_db import AdminBase

class NewsPost(AdminBase):
    __tablename__ = "news_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    

    author_id = Column(Integer, index=True)  # vem do auth_db
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    
    # Sistema de aprovação
    status = Column(String(20), default="pending", index=True)  # "pending", "approved", "rejected", "deleted"
    approved_by_id = Column(Integer, nullable=True)  # ID do admin/admin_master que aprovou
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by_id = Column(Integer, nullable=True)  # ID do admin/admin_master que rejeitou
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    
    # Sistema de soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_id = Column(Integer, nullable=True)  # ID do usuário que deletou
    
    # Flag para eventos que requerem aprovação
    requires_approval = Column(Boolean, default=True)  # Se False, post vai direto pro feed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    event = relationship("Event", back_populates="news_posts")
    images = relationship("NewsImage", back_populates="news", cascade="all, delete-orphan", order_by="NewsImage.image_order")

    __table_args__ = (
        # Índices individuais (mantidos para compatibilidade e queries simples)
        Index("idx_news_posts_event_id", "event_id"),
        Index("idx_news_posts_author_id", "author_id"),
        Index("idx_news_posts_status", "status"),
        
        # Índice composto otimizado: event_id primeiro (mais seletivo), depois status, depois deleted_at
        # Ordem ideal para queries: WHERE event_id = X AND status = Y AND deleted_at IS NULL
        Index("idx_news_posts_event_status_deleted", "event_id", "status", "deleted_at"),
        
        # Índice composto alternativo para queries que filtram por status primeiro
        # Útil para: WHERE status = 'approved' AND deleted_at IS NULL (sem filtro por event_id)
        Index("idx_news_posts_status_deleted", "status", "deleted_at"),
        
        # Índice composto para consultas por autor e evento
        Index("idx_news_posts_author_event", "author_id", "event_id"),
        
        # Índice composto para consultas por autor, status e deleted_at
        # Útil para: WHERE author_id = X AND status = Y AND deleted_at IS NULL
        Index("idx_news_posts_author_status_deleted", "author_id", "status", "deleted_at"),
    )

