# app/domain/admin/models/event_model.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Time, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, time
from app.config.admin_db import AdminBase

class Event(AdminBase):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    banner_image = Column(String(500), nullable=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    event_dates = Column(String(500), nullable=True)  # Campo para múltiplas datas (formato: "2024-01-09,2024-01-10,2024-01-20,2024-01-21")
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, nullable=True)  # ID do usuário que criou o evento
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)  # Data e hora da última atualização
    updated_by_id = Column(Integer, nullable=True)  # ID do usuário que realizou a última atualização
    is_active = Column(Boolean, default=True, nullable=False)
    location = Column(String(255), nullable=True)
    image_map = Column(String(500), nullable=True)
    camping_map_url = Column(String(500), nullable=True)
    line_up = Column(Text, nullable=True)
    spotify_playlist_url = Column(String(500), nullable=True)
    requires_post_approval = Column(Boolean, default=True)  # Se True, posts precisam aprovação
    van_arrival_time_start = Column(Time, nullable=True)  # Horário de início da ida das vans (ex: 19:00)
    van_arrival_time_end = Column(Time, nullable=True)  # Horário de fim da ida das vans (ex: 23:00)
    van_departure_time_start = Column(Time, nullable=True)  # Horário de início da volta das vans (ex: 00:00)
    van_departure_time_end = Column(Time, nullable=True)  # Horário de fim da volta das vans (ex: 07:00)
    meeting_point_location = Column(String(255), nullable=True)  # Local do meeting point
    meeting_point_schedule = Column(JSON, nullable=True)  # Horários de funcionamento em formato JSON
    
    # Sistema de soft delete
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, nullable=True)  # ID do usuário que deletou
    
    news_posts = relationship(
        "NewsPost",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    map_images = relationship(
        "EventMapImage",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventMapImage.image_order"
    )

# Importar EventMapImage após a definição de Event para evitar importação circular
# mas garantir que o modelo esteja disponível quando o SQLAlchemy configurar os relacionamentos
from app.domain.admin.models.event_map_image_model import EventMapImage  # noqa: F401
from app.domain.admin.models.lineup_item_model import LineupItem  # noqa: F401
