"""
Worker de notificação para o navegador (Web Push).

Envia notificações ao navegador do usuário como um app envia notificação
no dispositivo: usa Web Push API com as assinaturas (push_subscriptions)
salvas para cada usuário. Respeita a preferência push_enabled.
"""
import logging
from app.infra.celery_app import celery_app
from app.config.notification_db import get_notification_db

logger = logging.getLogger(__name__)


def _build_notification_url(notification):
    """Monta URL opcional para abrir a notificação ou a tela de notificações."""
    base = "/pages/user/notifications"
    if not notification:
        return base
    # Deep link para a notificação específica (o front pode usar ?id= para scroll/foco)
    nid = getattr(notification, "id", None)
    if nid:
        return f"{base}?id={nid}"
    return base


@celery_app.task(name='notifications.send_push_for_notification', bind=True, max_retries=2)
def send_push_for_notification_task(self, notification_id: int):
    """
    Worker de notificação para o navegador: envia Web Push para todos os
    dispositivos inscritos do usuário (como notificação de app no dispositivo).
    Respeita push_enabled e usa as assinaturas salvas em push_subscriptions.
    """
    logger.info("[Push] Task recebida: notificação id=%s", notification_id)
    try:
        from app.domain.users.models.notification_model import Notification
        from app.domain.users.services.push_service import send_web_push_to_user

        notification_db = next(get_notification_db())
        try:
            notification = notification_db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            if not notification:
                logger.warning("[Push] Notificação id=%s não encontrada.", notification_id)
                return

            user_id = notification.user_id
            title = (notification.title or "")[:60]
            message = (notification.message or "")[:80]
            url = _build_notification_url(notification)

            sent = send_web_push_to_user(
                notification_db,
                user_id=user_id,
                title=title,
                message=message,
                url=url,
                notification_id=notification_id,
            )
            logger.info(
                "[Push] Notificação id=%s enviada ao navegador para user_id=%s (dispositivos=%s)",
                notification_id,
                user_id,
                sent,
            )
        finally:
            notification_db.close()
    except Exception as e:
        logger.exception("[Push] Erro ao enviar notificação %s: %s", notification_id, e)
        raise self.retry(exc=e, countdown=30)
