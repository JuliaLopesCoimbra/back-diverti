from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from app.config.auth_db import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    refresh_token = Column(String(255), unique=True)
    user_agent = Column(String(255))
    ip_address = Column(String(50))

    revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # Índice em user_id para consultas frequentes por usuário
        Index("idx_refresh_tokens_user_id", "user_id"),
        # Índice composto para consultas de tokens ativos por usuário
        Index("idx_refresh_tokens_user_revoked", "user_id", "revoked"),
    )
