from app.domain.users.repositories.comment_like_repository import CommentLikeRepository
from app.domain.users.services.comment_like_service import CommentLikeService
from fastapi import BackgroundTasks


class CommentLikeController:

    @staticmethod
    def create(interaction_db, admin_db, comment_id, user, ip_address: str = None, user_agent: str = None, background_tasks: BackgroundTasks = None):
        return CommentLikeService.add_like(
            interaction_db,
            admin_db,
            comment_id,
            user.id,
            ip_address,
            user_agent,
            background_tasks
        )
    
    @staticmethod
    def remove(interaction_db, comment_id, user, background_tasks: BackgroundTasks = None):
        # OTIMIZAÇÃO: Busca news_id do comentário de forma eficiente (apenas o campo necessário)
        from app.domain.users.models.comment_model import Comment
        news_id_result = interaction_db.query(Comment.news_id).filter(Comment.id == comment_id).first()
        news_id = news_id_result[0] if news_id_result else None
        
        CommentLikeRepository.remove(interaction_db, comment_id, user.id)
        
        # Invalidar cache em background (não bloqueia a resposta)
        if background_tasks:
            from app.domain.users.services.cache_background import invalidate_comment_cache_async
            if news_id:
                background_tasks.add_task(invalidate_comment_cache_async, news_id, user.id)
        
        # Remover notificação via fila Celery (processamento assíncrono)
        # IMPORTANTE: Sempre tenta enviar, mesmo se background_tasks não estiver disponível
        try:
            from app.domain.users.tasks.notification_tasks import remove_comment_like_notification_task
            remove_comment_like_notification_task.delay(comment_id, user.id)
        except Exception as e:
            # Se Celery não estiver disponível, loga erro mas não quebra a requisição
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao remover notificação de curtida de comentário via Celery: {e}", exc_info=True)
        
        return {
            "comment_id": comment_id,
            "liked": False,
            "message": "Curtida removida"
        }

    @staticmethod
    def count(interaction_db, comment_id: int):
        return {
            "comment_id": comment_id,
            "likes": CommentLikeService.get_likes_count(interaction_db, comment_id)
        }

    @staticmethod
    def get_users_who_liked(interaction_db, auth_db, comment_id: int, limit: int = 10, offset: int = 0):
        return CommentLikeService.get_users_who_liked(interaction_db, auth_db, comment_id, limit, offset)

