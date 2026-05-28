from pydantic import BaseModel
from typing import Optional

class NotificationPreferenceResponse(BaseModel):
    user_id: int
    lineup_updated: bool
    news_feed: bool
    interactions: bool
    new_events: bool
    push_enabled: bool = False

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    lineup_updated: Optional[bool] = None
    news_feed: Optional[bool] = None
    interactions: Optional[bool] = None
    new_events: Optional[bool] = None
    push_enabled: Optional[bool] = None

