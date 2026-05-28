"""Tasks do Celery para processamento assíncrono de notificações"""
from app.infra.celery_app import celery_app
from app.config.notification_db import get_notification_db
from app.config.auth_db import get_db
from app.config.admin_db import get_admin_db
from app.config.interaction_db import get_interaction_db
from app.domain.users.services.notification_service import NotificationService
import logging

# IMPORTANTE: Importar todos os modelos necessários para que o SQLAlchemy
# possa configurar corretamente os relacionamentos no contexto do Celery
# Isso resolve o erro "Event failed to locate a name"
# Os imports devem ser feitos ANTES de qualquer uso dos modelos nas tasks
from app.domain.admin.models.news_model import NewsPost  # noqa: F401
from app.domain.admin.models.event_model import Event  # noqa: F401
from app.domain.admin.models.news_image_model import NewsImage  # noqa: F401
from app.domain.auth.models.user_model import User  # noqa: F401
from app.domain.users.models.comment_model import Comment  # noqa: F401
from app.domain.users.models.comment_like_model import CommentLike  # noqa: F401

logger = logging.getLogger(__name__)


@celery_app.task(name='notifications.notify_post_like', bind=True, max_retries=3)
def notify_post_like_task(self, news_id: int, liker_id: int):
    """
    Task Celery para criar notificação de curtida de post
    
    Args:
        news_id: ID do post curtido
        liker_id: ID do usuário que curtiu
    """
    # logger.info(f"🔄 Task recebida: notify_post_like - news_id={news_id}, liker_id={liker_id}")
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        admin_db = next(get_admin_db())
        try:
            # logger.info(f"📝 Chamando NotificationService.notify_post_like...")
            NotificationService.notify_post_like(
                notification_db, auth_db, admin_db, news_id, liker_id
            )
            # logger.info(f"✅ Notificação de curtida de post criada com sucesso: news_id={news_id}, liker_id={liker_id}")
        finally:
            notification_db.close()
            auth_db.close()
            admin_db.close()
    except Exception as e:
        logger.error(f"Erro ao criar notificação de curtida de post: {e}", exc_info=True)
        # print(f"❌ ERRO na task notify_post_like: {e}")  # Debug no console
        # Retry automático em caso de erro
        raise self.retry(exc=e, countdown=60)  # Tenta novamente em 60 segundos


@celery_app.task(name='notifications.notify_post_comment', bind=True, max_retries=3)
def notify_post_comment_task(self, news_id: int, comment_id: int, comment_author_id: int):
    """
    Task Celery para criar notificação de comentário no post
    
    Args:
        news_id: ID do post comentado
        comment_id: ID do comentário criado
        comment_author_id: ID do autor do comentário
    """
    # logger.info(f"🔄 Task recebida: notify_post_comment - news_id={news_id}, comment_id={comment_id}, comment_author_id={comment_author_id}")
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        admin_db = next(get_admin_db())
        try:
            # logger.info(f"📝 Chamando NotificationService.notify_post_comment...")
            NotificationService.notify_post_comment(
                notification_db, auth_db, admin_db, news_id, comment_id, comment_author_id
            )
            # logger.info(f"✅ Notificação de comentário no post criada com sucesso: news_id={news_id}, comment_id={comment_id}")
        finally:
            notification_db.close()
            auth_db.close()
            admin_db.close()
    except Exception as e:
        logger.error(f"Erro ao criar notificação de comentário no post: {e}", exc_info=True)
        # print(f"❌ ERRO na task notify_post_comment: {e}")  # Debug no console
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='notifications.notify_comment_reply', bind=True, max_retries=3)
def notify_comment_reply_task(self, parent_comment_id: int, reply_author_id: int, reply_id: int):
    """
    Task Celery para criar notificação de resposta a comentário
    
    Args:
        parent_comment_id: ID do comentário pai
        reply_author_id: ID do autor da resposta
        reply_id: ID da resposta criada
    """
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        interaction_db = next(get_interaction_db())
        try:
            NotificationService.notify_comment_reply(
                notification_db, auth_db, interaction_db, parent_comment_id, reply_author_id, reply_id
            )
            logger.info(f"Notificação de resposta a comentário criada: parent_comment_id={parent_comment_id}, reply_id={reply_id}")
        finally:
            notification_db.close()
            auth_db.close()
            interaction_db.close()
    except Exception as e:
        logger.error(f"Erro ao criar notificação de resposta a comentário: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='notifications.notify_comment_like', bind=True, max_retries=3)
def notify_comment_like_task(self, comment_id: int, liker_id: int):
    """
    Task Celery para criar notificação de curtida de comentário
    
    Args:
        comment_id: ID do comentário curtido
        liker_id: ID do usuário que curtiu
    """
    # logger.info(f"🔄 Task recebida: notify_comment_like - comment_id={comment_id}, liker_id={liker_id}")
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        interaction_db = next(get_interaction_db())
        try:
            # logger.info(f"📝 Chamando NotificationService.notify_comment_like...")
            NotificationService.notify_comment_like(
                notification_db, auth_db, interaction_db, comment_id, liker_id
            )
            # logger.info(f"✅ Notificação de curtida de comentário criada com sucesso: comment_id={comment_id}, liker_id={liker_id}")
        finally:
            notification_db.close()
            auth_db.close()
            interaction_db.close()
    except Exception as e:
        logger.error(f"Erro ao criar notificação de curtida de comentário: {e}", exc_info=True)
        # print(f"❌ ERRO na task notify_comment_like: {e}")  # Debug no console
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='notifications.remove_post_like_notification', bind=True, max_retries=3)
def remove_post_like_notification_task(self, news_id: int, liker_id: int):
    """
    Task Celery para remover notificação de curtida de post
    
    Args:
        news_id: ID do post
        liker_id: ID do usuário que descurtiu
    """
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        admin_db = next(get_admin_db())
        try:
            NotificationService.remove_post_like_notification(
                notification_db, admin_db, news_id, liker_id, auth_db
            )
            logger.info(f"Notificação de curtida de post removida: news_id={news_id}, liker_id={liker_id}")
        finally:
            notification_db.close()
            auth_db.close()
            admin_db.close()
    except Exception as e:
        logger.error(f"Erro ao remover notificação de curtida de post: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='notifications.remove_comment_like_notification', bind=True, max_retries=3)
def remove_comment_like_notification_task(self, comment_id: int, liker_id: int):
    """
    Task Celery para remover notificação de curtida de comentário
    
    Args:
        comment_id: ID do comentário
        liker_id: ID do usuário que descurtiu
    """
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        interaction_db = next(get_interaction_db())
        try:
            NotificationService.remove_comment_like_notification(
                notification_db, interaction_db, comment_id, liker_id, auth_db
            )
            logger.info(f"Notificação de curtida de comentário removida: comment_id={comment_id}, liker_id={liker_id}")
        finally:
            notification_db.close()
            auth_db.close()
            interaction_db.close()
    except Exception as e:
        logger.error(f"Erro ao remover notificação de curtida de comentário: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='notifications.notify_new_event', bind=True, max_retries=3)
def notify_new_event_task(self, event_id: int):
    """
    Task Celery para criar notificações de novo evento
    
    Args:
        event_id: ID do evento criado
    """
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        admin_db = next(get_admin_db())
        try:
            NotificationService.notify_new_event(
                notification_db, auth_db, admin_db, event_id
            )
            logger.info(f"Notificações de novo evento criadas: event_id={event_id}")
        finally:
            notification_db.close()
            auth_db.close()
            admin_db.close()
    except Exception as e:
        logger.error(f"Erro ao criar notificações de novo evento: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='notifications.restore_event_notifications', bind=True, max_retries=3)
def restore_event_notifications_task(self, event_id: int):
    """
    Task Celery para restaurar notificações quando evento volta ativo
    
    Args:
        event_id: ID do evento que foi ativado
    """
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        admin_db = next(get_admin_db())
        try:
            NotificationService.restore_event_notifications(
                notification_db, auth_db, admin_db, event_id
            )
            logger.info(f"Notificações de evento restauradas: event_id={event_id}")
        finally:
            notification_db.close()
            auth_db.close()
            admin_db.close()
    except Exception as e:
        logger.error(f"Erro ao restaurar notificações de evento: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='notifications.notify_new_post', bind=True, max_retries=3)
def notify_new_post_task(self, news_id: int, event_id: int):
    """
    Task Celery para criar notificações de novo post no feed
    
    Args:
        news_id: ID do post publicado
        event_id: ID do evento relacionado
    """
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        admin_db = next(get_admin_db())
        try:
            NotificationService.notify_new_post(
                notification_db, auth_db, admin_db, news_id, event_id
            )
            logger.info(f"Notificações de novo post criadas: news_id={news_id}, event_id={event_id}")
        finally:
            notification_db.close()
            auth_db.close()
            admin_db.close()
    except Exception as e:
        logger.error(f"Erro ao criar notificações de novo post: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='notifications.notify_lineup_updated', bind=True, max_retries=3)
def notify_lineup_updated_task(self, event_id: int):
    """
    Task Celery para criar notificações de atualização de line up
    
    Args:
        event_id: ID do evento com line up atualizado
    """
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        admin_db = next(get_admin_db())
        try:
            NotificationService.notify_lineup_updated(
                notification_db, auth_db, admin_db, event_id
            )
            logger.info(f"Notificações de line up atualizado criadas: event_id={event_id}")
        finally:
            notification_db.close()
            auth_db.close()
            admin_db.close()
    except Exception as e:
        logger.error(f"Erro ao criar notificações de line up atualizado: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(name='notifications.broadcast_notification', bind=True, max_retries=3)
def broadcast_notification_task(self, title: str, message: str, sender_id: int):
    """
    Task Celery para enviar notificação personalizada (broadcast) para todos os usuários
    
    Args:
        title: Título da notificação
        message: Mensagem da notificação
        sender_id: ID do admin/subadmin que está enviando a notificação
    """
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        try:
            users_notified = NotificationService.broadcast_notification(
                notification_db, auth_db, title, message, sender_id
            )
            logger.info(f"Notificação broadcast enviada para {users_notified} usuários pelo sender_id {sender_id}")
            return users_notified
        finally:
            notification_db.close()
            auth_db.close()
    except Exception as e:
        logger.error(f"Erro ao enviar notificação broadcast: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)
