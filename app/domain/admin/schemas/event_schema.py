from pydantic import BaseModel
from datetime import datetime, time
from typing import Optional, List, Dict, Any


class EventMapImageSchema(BaseModel):
    id: int
    event_id: int
    image_url: str
    image_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class EventCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    banner_image: Optional[str] = None
    image_map: Optional[str] = None
    line_up: Optional[str] = None
    spotify_playlist_url: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    event_dates: Optional[str] = None  # Formato: "2024-01-09,2024-01-10,2024-01-20,2024-01-21"
    van_arrival_time_start: Optional[time] = None  # Horário de início da ida (ex: 19:00)
    van_arrival_time_end: Optional[time] = None  # Horário de fim da ida (ex: 23:00)
    van_departure_time_start: Optional[time] = None  # Horário de início da volta (ex: 00:00)
    van_departure_time_end: Optional[time] = None  # Horário de fim da volta (ex: 07:00)
    meeting_point_location: Optional[str] = None  # Local do meeting point
    meeting_point_schedule: Optional[List[Dict[str, Any]]] = None  # Horários de funcionamento em formato JSON


class EventResponseSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    banner_image: Optional[str] = None
    image_map: Optional[str] = None
    line_up: Optional[str] = None
    spotify_playlist_url: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    event_dates: Optional[str] = None  # Formato: "2024-01-09,2024-01-10,2024-01-20,2024-01-21"
    van_arrival_time_start: Optional[time] = None  # Horário de início da ida (ex: 19:00)
    van_arrival_time_end: Optional[time] = None  # Horário de fim da ida (ex: 23:00)
    van_departure_time_start: Optional[time] = None  # Horário de início da volta (ex: 00:00)
    van_departure_time_end: Optional[time] = None  # Horário de fim da volta (ex: 07:00)
    meeting_point_location: Optional[str] = None  # Local do meeting point
    meeting_point_schedule: Optional[List[Dict[str, Any]]] = None  # Horários de funcionamento em formato JSON
    is_active: bool
    requires_post_approval: bool
    created_at: datetime
    created_by_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None
    map_images: Optional[List[EventMapImageSchema]] = []

    class Config:
        from_attributes = True

class EventUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    banner_image: Optional[str] = None
    image_map: Optional[str] = None
    line_up: Optional[str] = None
    spotify_playlist_url: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    event_dates: Optional[str] = None  # Formato: "2024-01-09,2024-01-10,2024-01-20,2024-01-21"
    van_arrival_time_start: Optional[time] = None  # Horário de início da ida (ex: 19:00)
    van_arrival_time_end: Optional[time] = None  # Horário de fim da ida (ex: 23:00)
    van_departure_time_start: Optional[time] = None  # Horário de início da volta (ex: 00:00)
    van_departure_time_end: Optional[time] = None  # Horário de fim da volta (ex: 07:00)
    meeting_point_location: Optional[str] = None  # Local do meeting point
    meeting_point_schedule: Optional[List[Dict[str, Any]]] = None  # Horários de funcionamento em formato JSON