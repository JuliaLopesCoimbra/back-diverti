from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SambaSchoolResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    image_url: Optional[str]
    event_id: int
    created_at: datetime
    created_by_id: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None
    deleted_at: Optional[datetime] = None
    deleted_by_id: Optional[int] = None

    class Config:
        from_attributes = True
