from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DownloadedPhotoResponse(BaseModel):
    id: int
    user_id: int
    image_url: str
    event_id: Optional[int] = None
    event_name: Optional[str] = None
    similarity: Optional[str] = None
    downloaded_at: datetime

    class Config:
        from_attributes = True

class CreateDownloadedPhotoRequest(BaseModel):
    image_url: str
    event_id: Optional[int] = None
    event_name: Optional[str] = None
    similarity: Optional[str] = None




