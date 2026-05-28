from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.config.admin_db import AdminBase

class MusicLyrics(AdminBase):
    __tablename__ = "music_lyrics"

    id = Column(Integer, primary_key=True, index=True)
    song_name = Column(String(255), nullable=False)
    singer = Column(String(255), nullable=True)
    lyrics = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, nullable=True)  # ID do usuário que criou a letra de música
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)  # Data e hora da última atualização
    updated_by_id = Column(Integer, nullable=True)  # ID do usuário que realizou a última atualização

    samba_school_id = Column(Integer, ForeignKey("samba_schools.id"), nullable=False)
    
    # Sistema de soft delete
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, nullable=True)  # ID do usuário que deletou

    samba_school = relationship("SambaSchool", backref="music_lyrics")
