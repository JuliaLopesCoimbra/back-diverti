from app.domain.users.repositories.comment_repository import CommentRepository
from app.domain.users.repositories.like_repository import LikeRepository
from app.domain.users.services.comment_service import CommentService
from fastapi import BackgroundTasks


class CommentController:

    @staticmethod
    def create(interaction_db, auth_db, admin_db, content, news_id, user_id, parent_comment_id=None, background_tasks: BackgroundTasks = None):
        # Usa o serviço que retorna os dados formatados com informações do usuário
        result = CommentService.add_comment(interaction_db, auth_db, admin_db, news_id, content, user_id, parent_comment_id)
        
        # Invalidar cache em background (não bloqueia a resposta)
        if background_tasks and result:
            from app.domain.users.services.cache_background import invalidate_comment_cache_async
            background_tasks.add_task(invalidate_comment_cache_async, news_id, user_id)
        
        # Criar notificações via Celery (processamento assíncrono)
        # IMPORTANTE: Não depende de background_tasks, sempre tenta enviar
        if result:
            try:
                import logging
                logger = logging.getLogger(__name__)
                
                if parent_comment_id:
                    # É uma resposta a outro comentário
                    from app.domain.users.tasks.notification_tasks import notify_comment_reply_task
                    task_result = notify_comment_reply_task.delay(parent_comment_id, user_id, result.get("id"))
                    # logger.info(f"✅ Task enviada para Celery: notify_comment_reply - Task ID: {task_result.id}, parent_comment_id={parent_comment_id}, user_id={user_id}, reply_id={result.get('id')}")
                else:
                    # É um comentário principal no post
                    from app.domain.users.tasks.notification_tasks import notify_post_comment_task
                    task_result = notify_post_comment_task.delay(news_id, result.get("id"), user_id)
                    # logger.info(f"✅ Task enviada para Celery: notify_post_comment - Task ID: {task_result.id}, news_id={news_id}, comment_id={result.get('id')}, user_id={user_id}")
            except Exception as e:
                # Se Celery não estiver disponível, loga erro mas não quebra a requisição
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erro ao enviar notificação para Celery: {e}", exc_info=True)
                # print(f"❌ ERRO ao enviar notificação para Celery: {e}")  # Debug no console
        
        return result

    @staticmethod
    def list(interaction_db, news_id, auth_db, user_id=None, parent_comment_id=None, limit: int = 50, offset: int = 0):
        return CommentService.list_comments(interaction_db, news_id, auth_db, user_id, parent_comment_id, limit, offset)

    @staticmethod
    def get_likes_count(interaction_db, news_id: int) -> int:
        return LikeRepository.count_by_news(interaction_db, news_id)
    
    @staticmethod
    def delete(interaction_db, comment_id: int, user_id: int, user_role: str):
        """Deleta um comentário (soft delete)"""
        return CommentService.delete_comment(interaction_db, comment_id, user_id, user_role)

