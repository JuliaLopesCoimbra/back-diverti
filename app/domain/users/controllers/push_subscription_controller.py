from fastapi import HTTPException
from app.domain.users.repositories.push_subscription_repository import PushSubscriptionRepository
from app.domain.users.schemas.notification_schema import PushSubscriptionRequest, PushSubscriptionUnregisterRequest


class PushSubscriptionController:
    @staticmethod
    def register(notification_db, user_id: int, data: PushSubscriptionRequest):
        """Registra ou atualiza assinatura Web Push do usuário."""
        sub = PushSubscriptionRepository.create(
            notification_db,
            user_id=user_id,
            endpoint=data.endpoint,
            p256dh=data.keys.p256dh,
            auth=data.keys.auth,
            user_agent=data.user_agent,
        )
        return {"message": "Assinatura de notificações no dispositivo ativada", "id": sub.id}

    @staticmethod
    def unregister(notification_db, user_id: int, data: PushSubscriptionUnregisterRequest):
        """Remove assinatura Web Push do usuário."""
        removed = PushSubscriptionRepository.delete_by_endpoint(
            notification_db, data.endpoint, user_id
        )
        if not removed:
            raise HTTPException(status_code=404, detail="Assinatura não encontrada")
        return {"message": "Assinatura removida"}