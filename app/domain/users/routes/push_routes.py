"""Rotas para Web Push: inscrição e chave pública VAPID."""
from fastapi import APIRouter, Depends
from app.core.security.auth_dependency import get_current_user
from app.config.notification_db import get_notification_db
from app.config.settings import settings
from app.domain.auth.models.user_model import User
from app.domain.users.controllers.push_subscription_controller import PushSubscriptionController
from app.domain.users.schemas.notification_schema import (
    PushSubscriptionRequest,
    PushSubscriptionUnregisterRequest,
)

router = APIRouter(prefix="/notifications", tags=["Push (notificações no dispositivo)"])


@router.get("/vapid-public-key")
def get_vapid_public_key():
    """Retorna a chave pública VAPID para o frontend inscrever o navegador em Web Push."""
    key = getattr(settings, "VAPID_PUBLIC_KEY", None) or ""
    return {"vapid_public_key": key}


@router.post("/push/subscribe")
def push_subscribe(
    data: PushSubscriptionRequest,
    notification_db=Depends(get_notification_db),
    user: User = Depends(get_current_user),
):
    """Registra a assinatura Web Push do navegador do usuário (para receber notificações no dispositivo)."""
    return PushSubscriptionController.register(notification_db, user.id, data)


@router.post("/push/unsubscribe")
def push_unsubscribe(
    data: PushSubscriptionUnregisterRequest,
    notification_db=Depends(get_notification_db),
    user: User = Depends(get_current_user),
):
    """Remove a assinatura Web Push do navegador do usuário."""
    return PushSubscriptionController.unregister(notification_db, user.id, data)
