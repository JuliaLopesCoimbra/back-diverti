"""Serviço para criar notificações em background (não bloqueia a resposta da API)"""
from app.config.notification_db import get_notification_db
from app.config.auth_db import get_db
from app.config.admin_db import get_admin_db
from app.config.interaction_db import get_interaction_db
from app.domain.users.services.notification_service import NotificationService

def notify_comment_like_async(comment_id: int, liker_id: int):
    """Cria notificação de curtida de comentário em background"""
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        interaction_db = next(get_interaction_db())
        try:
            NotificationService.notify_comment_like(
                notification_db, auth_db, interaction_db, comment_id, liker_id
            )
        finally:
            notification_db.close()
            auth_db.close()
            interaction_db.close()
    except Exception as e:
        print(f"Erro ao criar notificação de curtida de comentário em background: {e}")

def notify_comment_reply_async(parent_comment_id: int, reply_author_id: int, reply_id: int):
    """Cria notificação de resposta a comentário em background"""
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        interaction_db = next(get_interaction_db())
        try:
            NotificationService.notify_comment_reply(
                notification_db, auth_db, interaction_db, parent_comment_id, reply_author_id, reply_id
            )
        finally:
            notification_db.close()
            auth_db.close()
            interaction_db.close()
    except Exception as e:
        print(f"Erro ao criar notificação de resposta em background: {e}")

def notify_post_comment_async(news_id: int, comment_id: int, comment_author_id: int):
    """Cria notificação de comentário no post em background"""
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        admin_db = next(get_admin_db())
        try:
            NotificationService.notify_post_comment(
                notification_db, auth_db, admin_db, news_id, comment_id, comment_author_id
            )
        finally:
            notification_db.close()
            auth_db.close()
            admin_db.close()
    except Exception as e:
        print(f"Erro ao criar notificação de comentário no post em background: {e}")

def notify_post_like_async(news_id: int, liker_id: int):
    """Cria notificação de curtida de post em background"""
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        admin_db = next(get_admin_db())
        try:
            NotificationService.notify_post_like(
                notification_db, auth_db, admin_db, news_id, liker_id
            )
        finally:
            notification_db.close()
            auth_db.close()
            admin_db.close()
    except Exception as e:
        print(f"Erro ao criar notificação de curtida de post em background: {e}")

def remove_comment_like_notification_async(comment_id: int, liker_id: int):
    """Remove notificação de curtida de comentário em background"""
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        interaction_db = next(get_interaction_db())
        try:
            NotificationService.remove_comment_like_notification(
                notification_db, interaction_db, comment_id, liker_id, auth_db
            )
        finally:
            notification_db.close()
            auth_db.close()
            interaction_db.close()
    except Exception as e:
        print(f"Erro ao remover notificação de curtida de comentário em background: {e}")

def remove_post_like_notification_async(news_id: int, liker_id: int):
    """Remove notificação de curtida de post em background"""
    try:
        notification_db = next(get_notification_db())
        auth_db = next(get_db())
        admin_db = next(get_admin_db())
        try:
            NotificationService.remove_post_like_notification(
                notification_db, admin_db, news_id, liker_id, auth_db
            )
        finally:
            notification_db.close()
            auth_db.close()
            admin_db.close()
    except Exception as e:
        print(f"Erro ao remover notificação de curtida de post em background: {e}")

