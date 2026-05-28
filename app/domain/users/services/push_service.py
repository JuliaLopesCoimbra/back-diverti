import json
import logging
from typing import Optional

from app.config.settings import settings
from app.domain.users.repositories.push_subscription_repository import PushSubscriptionRepository
from app.domain.users.repositories.notification_preference_repository import NotificationPreferenceRepository

logger = logging.getLogger(__name__)


def _get_vapid_private_key():
    """
    Retorna a chave privada VAPID para o pywebpush.
    Deve ser: path do arquivo .pem (recomendado) OU string PEM começando com -----.
    O pywebpush usa Vapid.from_file(path) quando recebe path, e from_string quando recebe PEM.
    """
    import os
    key = (getattr(settings, "VAPID_PRIVATE_KEY", None) or "").strip()
    if not key:
        return None
    # Conteúdo PEM direto no .env
    if key.startswith("-----"):
        return key
    # Path para arquivo: retornar o path para pywebpush usar Vapid.from_file()
    if os.path.isfile(key):
        return key
    return key


def send_web_push_to_user(
    notification_db,
    user_id: int,
    title: str,
    message: str,
    url: Optional[str] = None,
    notification_id: Optional[int] = None,
) -> int:
    """
    Envia Web Push para todos os dispositivos inscritos do usuário.
    Respeita a preferência push_enabled.
    Retorna quantidade de pushes enviados com sucesso.
    """
    logger.info("[Push] --- send_web_push_to_user: user_id=%s title=%r notif_id=%s", user_id, (title or "")[:40], notification_id)

    vapid_key = _get_vapid_private_key()
    if not vapid_key:
        logger.warning("[Push] VAPID_PRIVATE_KEY não configurada no .env; push não enviado (user_id=%s).", user_id)
        return 0
    logger.info("[Push] VAPID_PRIVATE_KEY: configurada.")

    preference = NotificationPreferenceRepository.get_or_create(notification_db, user_id)
    push_enabled = getattr(preference, "push_enabled", False)
    logger.info("[Push] Preferência push_enabled para user_id=%s: %s", user_id, push_enabled)
    if not push_enabled:
        logger.info("[Push] push_enabled=False; push não enviado para user_id=%s.", user_id)
        return 0

    subscriptions = PushSubscriptionRepository.get_by_user_id(notification_db, user_id)
    logger.info("[Push] Assinaturas (dispositivos) para user_id=%s: %d encontrada(s).", user_id, len(subscriptions) if subscriptions else 0)
    if not subscriptions:
        logger.warning("[Push] Nenhuma assinatura (endpoint) para user_id=%s; push não enviado. Usuário aceitou no navegador mas a inscrição pode não ter sido salva.", user_id)
        return 0

    for i, sub in enumerate(subscriptions, 1):
        ua = (sub.user_agent or "?")[:80]
        ep = (sub.endpoint or "")[:100]
        logger.info("[Push] Para quem enviar: user_id=%s → dispositivo %d/%d | user_agent=%s | endpoint=%s...", user_id, i, len(subscriptions), ua, ep)

    try:
        from pywebpush import webpush, WebPushException
    except ImportError as e:
        logger.warning("[Push] pywebpush não instalado; Web Push desabilitado. %s", e)
        return 0

    payload = {
        "title": title,
        "body": message,
        "url": url or "/pages/user/notifications",
        "notification_id": notification_id,
    }
    data_json = json.dumps(payload)
    vapid_claims = {"sub": f"mailto:{getattr(settings, 'MAIL_FROM', 'noreply@n1app.com.br')}"}
    sent = 0
    for idx, sub in enumerate(subscriptions, 1):
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=data_json,
                vapid_private_key=vapid_key,
                vapid_claims=vapid_claims,
            )
            sent += 1
            logger.info("[Push] Enviado com sucesso para dispositivo %d/%d (user_id=%s) endpoint=%s...", idx, len(subscriptions), user_id, (sub.endpoint or "")[:80])
        except WebPushException as e:
            if e.response and e.response.status_code in (404, 410):
                logger.warning("[Push] Dispositivo %d/%d: assinatura expirada (404/410), endpoint=%s...", idx, len(subscriptions), (sub.endpoint or "")[:80])
            else:
                logger.warning("[Push] Erro ao enviar para dispositivo %d/%d: %s | endpoint=%s...", idx, len(subscriptions), e, (sub.endpoint or "")[:80])
        except Exception as e:
            logger.warning("[Push] Erro inesperado ao enviar para dispositivo %d/%d: %s", idx, len(subscriptions), e)
    logger.info("[Push] --- Fim send_web_push_to_user: user_id=%s total_enviados=%d de %d", user_id, sent, len(subscriptions))
    return sent
