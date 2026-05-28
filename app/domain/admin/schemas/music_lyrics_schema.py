from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MusicLyricsResponseSchema(BaseModel):
    id: int
    song_name: str
    singer: Optional[str]
    lyrics: str
    image_url: Optional[str]
    samba_school_id: int
    created_at: datetime
    created_by_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None

    class Config:
        from_attributes = True
