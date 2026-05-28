from app.domain.users.repositories.comment_like_repository import CommentLikeRepository
from sqlalchemy.exc import IntegrityError
from fastapi import BackgroundTasks

class CommentLikeService:

    @staticmethod
    def add_like(interaction_db, admin_db, comment_id: int, user_id: int, ip_address: str = None, user_agent: str = None, background_tasks: BackgroundTasks = None):
        # OTIMIZAÇÃO: Busca news_id do comentário de forma eficiente (apenas o campo necessário)
        from app.domain.users.models.comment_model import Comment
        news_id_result = interaction_db.query(Comment.news_id).filter(Comment.id == comment_id).first()
        news_id = news_id_result[0] if news_id_result else None
        
        try:
            CommentLikeRepository.create(
                interaction_db,
                comment_id,
                user_id,
                ip_address,
                user_agent,
                interaction_db,
                admin_db
            )
            
            # Invalidar cache em background (não bloqueia a resposta)
            if background_tasks:
                from app.domain.users.services.cache_background import invalidate_comment_cache_async
                if news_id:
                    background_tasks.add_task(invalidate_comment_cache_async, news_id, user_id)
            
            # Enviar notificação para fila Celery (processamento assíncrono)
            # IMPORTANTE: Sempre tenta enviar, mesmo se background_tasks não estiver disponível
            try:
                import logging
                logger = logging.getLogger(__name__)
                from app.domain.users.tasks.notification_tasks import notify_comment_like_task
                task_result = notify_comment_like_task.delay(comment_id, user_id)
                # logger.info(f"✅ Task enviada para Celery: notify_comment_like - Task ID: {task_result.id}, comment_id={comment_id}, liker_id={user_id}")
                # print(f"✅ Task enviada para Celery: notify_comment_like - Task ID: {task_result.id}")  # Debug no console
            except Exception as e:
                # Se Celery não estiver disponível, loga erro mas não quebra a requisição
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erro ao enviar notificação de curtida de comentário para Celery: {e}", exc_info=True)
                # print(f"❌ ERRO ao enviar notificação de curtida de comentário para Celery: {e}")  # Debug no console
            
            return {
                "comment_id": comment_id,
                "liked": True,
                "message": "Comentário curtido"
            }

        except IntegrityError as e:
            # Se ainda houver constraint único (caso a migração não tenha sido executada),
            # verifica se já existe like ativo e retorna mensagem apropriada
            interaction_db.rollback()
            
            # Verifica se já existe um like ativo
            existing = CommentLikeRepository.get_like(interaction_db, comment_id, user_id)
            if existing:
                return {
                    "comment_id": comment_id,
                    "liked": True,
                    "message": "Comentário já curtido"
                }
            
            # Se não existe, re-lança o erro (pode ser outro problema)
            raise

    @staticmethod
    def get_likes_count(interaction_db, comment_id: int) -> int:
        return CommentLikeRepository.count_by_comment(interaction_db, comment_id)

    @staticmethod
    def get_users_who_liked(interaction_db, auth_db, comment_id: int, limit: int = 10, offset: int = 0):
        """Retorna lista de usuários que curtiram um comentário, com paginação."""
        return CommentLikeRepository.get_users_who_liked(interaction_db, auth_db, comment_id, limit, offset)

