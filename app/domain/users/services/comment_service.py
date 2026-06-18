from app.domain.users.repositories.comment_repository import CommentRepository
from app.domain.users.repositories.comment_like_repository import CommentLikeRepository
from app.domain.auth.models.user_model import User
from app.infra.redis import redis_client, CacheKeys

class CommentService:

    @staticmethod
    def add_comment(interaction_db, auth_db, admin_db, news_id, content, user_id, parent_comment_id=None):
        comment = CommentRepository.create(
            interaction_db,
            content,
            news_id,
            user_id,
            parent_comment_id,
            admin_db
        )
        
        # Invalidação de cache será feita em background (não bloqueia a resposta)
        # A invalidação é feita através do CommentController que recebe background_tasks
        
        # Busca usuário de forma otimizada (já está na sessão se foi usado recentemente)
        user = auth_db.query(User).filter(User.id == user_id).first()

        if not user:
            return None

        # Verifica se created_at existe no objeto comment
        created_at_value = None
        if hasattr(comment, 'created_at') and comment.created_at:
            created_at_value = comment.created_at.isoformat()
        
        # Buscar curtidas do comentário (query rápida com índice)
        likes_count = CommentLikeRepository.count_by_comment(interaction_db, comment.id)
        
        # Contar respostas (apenas se for comentário principal, query rápida com índice)
        replies_count = 0
        if parent_comment_id is None:
            replies_count = CommentRepository.count_replies(interaction_db, comment.id)
        
        deleted_at_value = None
        if hasattr(comment, 'deleted_at') and comment.deleted_at:
            deleted_at_value = comment.deleted_at.isoformat()
        
        deleted_by_user_id_value = None
        if hasattr(comment, 'deleted_by_user_id') and comment.deleted_by_user_id:
            deleted_by_user_id_value = comment.deleted_by_user_id
        
        # Notificações serão criadas em background (não bloqueia a resposta)
        # As notificações são criadas através do CommentController que recebe background_tasks
        
        return {
            "id": comment.id,
            "content": comment.content,
            "created_at": created_at_value,
            "parent_comment_id": comment.parent_comment_id,
            "deleted_at": deleted_at_value,
            "deleted_by_user_id": deleted_by_user_id_value,
            "likes": {
                "count": likes_count,
                "user_liked": False
            },
            "replies_count": replies_count,
            "user": {
                "id": user.id,
                "name": user.name,
                "profile_photo": user.profile_photo
            }
        }

    @staticmethod
    def list_comments(interaction_db, news_id, auth_db, user_id=None, parent_comment_id=None, limit: int = 50, offset: int = 0):
        """Lista comentários com cache e paginação obrigatória - OTIMIZADO para evitar N+1 queries"""
        # Cache apenas para comentários principais (parent_comment_id=None) e primeira página
        if parent_comment_id is None and offset == 0:
            cache_key = CacheKeys.comments_list(news_id, user_id)
            cached = redis_client.get(cache_key)
            if cached is not None:
                # Retorna apenas os comentários da página solicitada
                return cached[offset:offset + limit]

        # Busca comentários do banco
        comments = CommentRepository.list_all(interaction_db, news_id, parent_comment_id, limit, offset)
        
        if not comments:
            return []
        
        # OTIMIZAÇÃO: Busca todos os dados de uma vez (batch loading) para evitar N+1 queries
        comment_ids = [comment.id for comment in comments]
        user_ids = list(set([comment.user_id for comment in comments]))
        
        # 1. Busca todos os usuários de uma vez
        users_dict = {}
        if user_ids:
            users = auth_db.query(User).filter(User.id.in_(user_ids)).all()
            users_dict = {user.id: user for user in users}
        
        # 2. Busca todos os likes de uma vez (batch)
        # IMPORTANTE: Filtra apenas likes ativos (is_active = True)
        from app.domain.users.models.comment_like_model import CommentLike
        from sqlalchemy import func
        likes_counts = (
            interaction_db.query(CommentLike.comment_id, func.count(CommentLike.id).label('count'))
            .filter(CommentLike.comment_id.in_(comment_ids), CommentLike.is_active == True)
            .group_by(CommentLike.comment_id)
            .all()
        )
        likes_count_dict = {comment_id: count for comment_id, count in likes_counts}
        
        # 3. Busca comentários curtidos pelo usuário de uma vez (se autenticado)
        # IMPORTANTE: Filtra apenas likes ativos (is_active = True)
        liked_comment_ids = set()
        if user_id and comment_ids:
            liked_comments = (
                interaction_db.query(CommentLike.comment_id)
                .filter(
                    CommentLike.comment_id.in_(comment_ids),
                    CommentLike.user_id == user_id,
                    CommentLike.is_active == True
                )
                .all()
            )
            liked_comment_ids = {like[0] for like in liked_comments}
        
        # 4. Busca contagens de replies de uma vez (batch) - apenas se for comentários principais
        replies_count_dict = {}
        if parent_comment_id is None and comment_ids:
            from app.domain.users.models.comment_model import Comment
            replies_counts = (
                interaction_db.query(Comment.parent_comment_id, func.count(Comment.id).label('count'))
                .filter(
                    Comment.parent_comment_id.in_(comment_ids),
                    Comment.deleted_at.is_(None)
                )
                .group_by(Comment.parent_comment_id)
                .all()
            )
            replies_count_dict = {parent_id: count for parent_id, count in replies_counts}

        # 5. Monta o resultado usando os dados já carregados
        result = []
        for comment in comments:
            user = users_dict.get(comment.user_id)
            if not user:
                continue  # Pula comentários de usuários não encontrados
            
            # Verifica se created_at existe no objeto comment
            created_at_value = None
            if hasattr(comment, 'created_at') and comment.created_at:
                created_at_value = comment.created_at.isoformat()
            
            deleted_at_value = None
            if hasattr(comment, 'deleted_at') and comment.deleted_at:
                deleted_at_value = comment.deleted_at.isoformat()
            
            deleted_by_user_id_value = None
            if hasattr(comment, 'deleted_by_user_id') and comment.deleted_by_user_id:
                deleted_by_user_id_value = comment.deleted_by_user_id
            
            # Usa contagem do batch (ou 0 se não encontrado)
            likes_count = likes_count_dict.get(comment.id, 0)
            
            # Usa contagem de replies do batch (ou 0 se não encontrado)
            replies_count = replies_count_dict.get(comment.id, 0) if parent_comment_id is None else 0
            
            result.append({
                "id": comment.id,
                "content": comment.content,
                "created_at": created_at_value,
                "parent_comment_id": comment.parent_comment_id,
                "deleted_at": deleted_at_value,
                "deleted_by_user_id": deleted_by_user_id_value,
                "likes": {
                    "count": likes_count,
                    "user_liked": comment.id in liked_comment_ids
                },
                "replies_count": replies_count,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "profile_photo": user.profile_photo
                }
            })

        # Cacheia apenas comentários principais da primeira página por 15 minutos (cache mais agressivo)
        if parent_comment_id is None and offset == 0:
            cache_key = CacheKeys.comments_list(news_id, user_id)
            redis_client.set(cache_key, result, ttl=900)
        
        return result
    
    @staticmethod
    def delete_comment(interaction_db, comment_id: int, user_id: int, user_role: str):
        """Deleta um comentário (soft delete) com validação de permissões"""
        from app.domain.users.repositories.comment_repository import CommentRepository
        
        comment = CommentRepository.get_by_id(interaction_db, comment_id)
        
        if not comment:
            raise ValueError("Comentário não encontrado.")
        
        # Verifica permissões: admin_master, admin ou dono do comentário podem deletar
        can_delete = (
            user_role in ["admin_master", "admin"] or 
            comment.user_id == user_id
        )
        
        if not can_delete:
            raise PermissionError("Você não tem permissão para excluir este comentário.")
        
        # Busca o comentário ANTES de deletar para obter informações necessárias
        comment_before_delete = CommentRepository.get_by_id(interaction_db, comment_id)
        comment_user_id = comment_before_delete.user_id if comment_before_delete else None
        parent_comment_id = comment_before_delete.parent_comment_id if comment_before_delete else None
        
        # Soft delete em cascata (passa o user_id para registrar quem deletou)
        CommentRepository.soft_delete_cascade(interaction_db, comment_id, user_id)
        
        # Remove notificações relacionadas a este comentário
        try:
            from app.config.notification_db import get_notification_db
            from app.config.auth_db import get_db
            from app.domain.users.services.notification_service import NotificationService
            notification_db = next(get_notification_db())
            auth_db = next(get_db())
            try:
                NotificationService.remove_comment_notifications(
                    notification_db, comment_id, interaction_db, auth_db,
                    comment_user_id, parent_comment_id
                )
            finally:
                notification_db.close()
                auth_db.close()
        except Exception as e:
            # Não quebra o fluxo se a remoção da notificação falhar
            print(f"Erro ao remover notificações do comentário: {e}")
        
        # Busca news_id do comentário para invalidar cache
        comment = comment_before_delete
        if comment:
            redis_client.delete(CacheKeys.comments_count(comment.news_id))
            redis_client.delete_pattern(f"comments:list:{comment.news_id}:*")
            redis_client.delete_pattern(f"news:details:{comment.news_id}:*")
        
        return {
            "message": "Comentário excluído com sucesso.",
            "comment_id": comment_id
        }
