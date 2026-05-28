from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RelatedUserInfo(BaseModel):
    id: int
    name: str
    profile_photo: Optional[str] = None
    
    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    message: str
    related_user_id: Optional[int] = None
    related_user: Optional[RelatedUserInfo] = None
    related_news_id: Optional[int] = None
    related_comment_id: Optional[int] = None
    related_event_id: Optional[int] = None
    broadcast_sender_id: Optional[int] = None
    broadcast_sender: Optional[RelatedUserInfo] = None
    count: int = 1  # Quantidade de pessoas que fizeram a ação (para agrupamento)
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    notifications: list[NotificationResponse]
    total: int
    unread_count: int

class UnreadCountResponse(BaseModel):
    unread_count: int

class BroadcastNotificationRequest(BaseModel):
    title: str
    message: str

class BroadcastNotificationResponse(BaseModel):
    message: str
    users_notified: int


# --- Web Push (notificações no navegador) ---
class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionRequest(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys
    user_agent: Optional[str] = None


class PushSubscriptionUnregisterRequest(BaseModel):
    endpoint: str

