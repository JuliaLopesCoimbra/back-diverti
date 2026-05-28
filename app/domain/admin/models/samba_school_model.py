from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.config.admin_db import AdminBase

class SambaSchool(AdminBase):
    __tablename__ = "samba_schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, nullable=True)  # ID do usuário que criou a escola de samba
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)  # Data e hora da última atualização
    updated_by_id = Column(Integer, nullable=True)  # ID do usuário que realizou a última atualização

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    
    # Sistema de soft delete
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, nullable=True)  # ID do usuário que deletou

    event = relationship("Event", backref="samba_schools")
