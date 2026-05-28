from fastapi import APIRouter, Depends, Query
from app.core.security.auth_dependency import get_current_user
from app.core.security.permissions import require_subadmin_or_master
from app.config.notification_db import get_notification_db
from app.config.auth_db import get_db
from app.domain.auth.models.user_model import User
from app.domain.users.controllers.notification_controller import NotificationController
from app.domain.users.schemas.notification_schema import (
    NotificationListResponse,
    UnreadCountResponse,
    BroadcastNotificationRequest,
    BroadcastNotificationResponse
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=NotificationListResponse)
def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    notification_db = Depends(get_notification_db),
    auth_db = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Lista notificações do usuário autenticado"""
    return NotificationController.list(notification_db, auth_db, user.id, limit, offset, unread_only)

@router.get("/unread/count", response_model=UnreadCountResponse)
def get_unread_count(
    notification_db = Depends(get_notification_db),
    user: User = Depends(get_current_user)
):
    """Retorna contagem de notificações não lidas"""
    return NotificationController.get_unread_count(notification_db, user.id)

@router.patch("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    notification_db = Depends(get_notification_db),
    auth_db = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Marca uma notificação como lida"""
    return NotificationController.mark_as_read(notification_db, auth_db, notification_id, user.id)

@router.patch("/read-all")
def mark_all_as_read(
    notification_db = Depends(get_notification_db),
    user: User = Depends(get_current_user)
):
    """Marca todas as notificações do usuário como lidas"""
    return NotificationController.mark_all_as_read(notification_db, user.id)

@router.post("/broadcast", response_model=BroadcastNotificationResponse)
def broadcast_notification(
    body: BroadcastNotificationRequest,
    notification_db = Depends(get_notification_db),
    auth_db = Depends(get_db),
    user: User = Depends(require_subadmin_or_master)
):
    """Envia uma notificação para todos os usuários ativos do sistema (apenas admin e subadmin)"""
    return NotificationController.broadcast(notification_db, auth_db, body, user.id)

