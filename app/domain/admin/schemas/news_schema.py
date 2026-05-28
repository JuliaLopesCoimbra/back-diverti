from fastapi import UploadFile
from pydantic import BaseModel
from typing import Optional, List

class NewsImageResponse(BaseModel):
    id: int
    image_url: str
    image_order: int

    class Config:
        from_attributes = True

class NewsCreate(BaseModel):
    title: str
    content: str
    image_url: str

class NewsResponse(BaseModel):
    id: int
    title: str
    content: str
    images: List[NewsImageResponse] = []
    created_at: str
    approved_at: Optional[str] = None
    deleted_at: Optional[str] = None
    deleted_by_id: Optional[int] = None
    event_id: Optional[int] = None
    status: Optional[str] = None  # "pending", "approved", "rejected", "deleted"

    class Config:
        from_attributes = True
