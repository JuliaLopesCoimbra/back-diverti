from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, JSON
from sqlalchemy.sql import func
from app.config.auth_db import Base
import enum

class EmailStatus(enum.Enum):
    PENDING = "pending"  # Aguardando envio
    SENT = "sent"  # Aceito pelo servidor SMTP
    FAILED = "failed"  # Falha no envio
    BOUNCED = "bounced"  # Rejeitado pelo servidor
    DELIVERED = "delivered"  # Entregue (via webhook)
    OPENED = "opened"  # Email foi aberto
    CLICKED = "clicked"  # Link foi clicado

class EmailType(enum.Enum):
    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"
    FIRST_ACCESS = "first_access"
    OTHER = "other"

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Destinatário
    user_id = Column(Integer, nullable=True, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    email_type = Column(Enum(EmailType), nullable=False, index=True)
    
    # Status e rastreamento
    status = Column(Enum(EmailStatus), default=EmailStatus.PENDING, index=True)
    
    # Informações de envio
    sent_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Erros e respostas
    error_message = Column(Text, nullable=True)
    smtp_response = Column(Text, nullable=True)
    server_response = Column(Text, nullable=True)
    
    # Rastreamento de entrega (webhooks)
    external_id = Column(String(255), nullable=True, index=True)  # ID do serviço externo
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True, index=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Metadados técnicos
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    message_id = Column(String(255), nullable=True, index=True)
    
    # Informações adicionais (JSON)
    extra_data = Column(JSON, nullable=True)  # Para armazenar dados extras (metadata é reservado pelo SQLAlchemy)
    
    # Validação pré-envio
    email_validated = Column(Boolean, default=False)
    validation_errors = Column(Text, nullable=True)
    mx_server = Column(String(255), nullable=True)

