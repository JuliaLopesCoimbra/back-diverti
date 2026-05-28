from app.domain.users.repositories.like_repository import LikeRepository
from app.domain.users.services.like_service import LikeService
from fastapi import BackgroundTasks


class LikeController:

    @staticmethod
    def create(interaction_db, admin_db, news_id, user, ip_address: str = None, user_agent: str = None, background_tasks: BackgroundTasks = None):
        result = LikeService.add_like(
            interaction_db,
            admin_db,
            news_id,
            user.id,
            ip_address,
            user_agent,
            background_tasks
        )
        
        # Invalidar cache em background (não bloqueia a resposta)
        if background_tasks:
            from app.domain.users.services.cache_background import invalidate_like_cache_async
            background_tasks.add_task(invalidate_like_cache_async, news_id, user.id)
        
        # Enviar notificação para fila Celery (processamento assíncrono)
        # IMPORTANTE: Sempre tenta enviar, mesmo se background_tasks não estiver disponível
        try:
            import logging
            logger = logging.getLogger(__name__)
            from app.domain.users.tasks.notification_tasks import notify_post_like_task
            task_result = notify_post_like_task.delay(news_id, user.id)
            # logger.info(f"✅ Task enviada para Celery: notify_post_like - Task ID: {task_result.id}, news_id={news_id}, liker_id={user.id}")
            # print(f"✅ Task enviada para Celery: notify_post_like - Task ID: {task_result.id}")  # Debug no console
        except Exception as e:
            # Se Celery não estiver disponível, loga erro mas não quebra a requisição
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao enviar notificação de curtida para Celery: {e}", exc_info=True)
            # print(f"❌ ERRO ao enviar notificação de curtida para Celery: {e}")  # Debug no console
        
        return result
    
    @staticmethod
    def remove(db, news_id, user, background_tasks: BackgroundTasks = None):
        result = LikeService.remove_like(db, news_id, user.id, background_tasks)
        
        # Invalidar cache em background (não bloqueia a resposta)
        if background_tasks:
            from app.domain.users.services.cache_background import invalidate_like_cache_async
            background_tasks.add_task(invalidate_like_cache_async, news_id, user.id)
        
        # Remover notificação via fila Celery (processamento assíncrono)
        # IMPORTANTE: Sempre tenta enviar, mesmo se background_tasks não estiver disponível
        try:
            from app.domain.users.tasks.notification_tasks import remove_post_like_notification_task
            remove_post_like_notification_task.delay(news_id, user.id)
        except Exception as e:
            # Se Celery não estiver disponível, loga erro mas não quebra a requisição
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao remover notificação de curtida via Celery: {e}", exc_info=True)
        
        return result

    @staticmethod
    def count(interaction_db, news_id: int):
        return {
            "news_id": news_id,
            "likes": LikeService.get_likes_count(interaction_db, news_id)
        }

    @staticmethod
    def get_liked_posts(admin_db, interaction_db, auth_db, user, event_id: int = None, limit: int = 10, offset: int = 0):
        return LikeService.get_liked_posts(
            admin_db,
            interaction_db,
            auth_db,
            user.id,
            event_id,
            limit,
            offset
        )

    @staticmethod
    def get_users_who_liked(interaction_db, auth_db, news_id: int, limit: int = 10, offset: int = 0):
        return LikeService.get_users_who_liked(interaction_db, auth_db, news_id, limit, offset)