# app/domain/users/repositories/comment_like_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from app.domain.users.models.comment_like_model import CommentLike

class CommentLikeRepository:

    @staticmethod
    def get_like(db: Session, comment_id: int, user_id: int):
        """Retorna o like ativo (is_active=True) para um usuário e comentário"""
        return db.query(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id,
            CommentLike.is_active == True
        ).first()

    @staticmethod
    def create(db: Session, comment_id: int, user_id: int, ip_address: str = None, user_agent: str = None, interaction_db: Session = None, admin_db: Session = None):
        """Sempre cria um NOVO registro de like para manter histórico completo.
        Se já existe um like ativo, retorna ele (evita duplicatas simultâneas).
        Caso contrário, cria um novo registro com timestamp atual."""
        # Verifica se já existe um like ativo (evita duplicatas em race conditions)
        existing_like = db.query(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id,
            CommentLike.is_active == True
        ).first()
        
        if existing_like:
            # Se já existe um like ativo, retorna ele (não cria duplicado simultâneo)
            # Isso evita problemas de race condition, mas mantém o histórico anterior
            return existing_like
        
        # Busca o event_id através do comentário -> notícia -> evento
        event_id = None
        if interaction_db is not None and admin_db is not None:
            from app.domain.users.models.comment_model import Comment
            from app.domain.admin.models.news_model import NewsPost
            
            # Busca o news_id do comentário
            comment = interaction_db.query(Comment.news_id).filter(Comment.id == comment_id).first()
            if comment:
                news_id = comment[0]
                # Busca o event_id da notícia
                news = admin_db.query(NewsPost.event_id).filter(NewsPost.id == news_id).first()
                if news:
                    event_id = news[0]
        
        # Sempre cria um NOVO registro para manter histórico completo
        # Mesmo que tenha existido um like antes, criamos um novo com novo timestamp
        like = CommentLike(
            comment_id=comment_id,
            user_id=user_id,
            event_id=event_id,
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True
        )
        db.add(like)
        db.commit()
        db.refresh(like)  # Garante que o objeto seja atualizado com o ID gerado
        return like

    @staticmethod
    def remove(db: Session, comment_id: int, user_id: int):
        """Marca o like mais recente como inativo (soft delete) em vez de deletar fisicamente.
        Isso preserva o histórico completo de todas as curtidas/descurtidas."""
        # Busca o like ativo mais recente (ordenado por created_at desc)
        like = db.query(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id,
            CommentLike.is_active == True
        ).order_by(CommentLike.created_at.desc()).first()
        
        if like:
            like.is_active = False
            like.deactivated_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False

    @staticmethod
    def count_by_comment(db: Session, comment_id: int) -> int:
        """Conta apenas likes ativos"""
        return db.query(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.is_active == True
        ).count()

    @staticmethod
    def get_liked_comment_ids(db: Session, user_id: int):
        """Retorna lista de comment_id que o usuário curtiu (apenas likes ativos)"""
        likes = db.query(CommentLike).filter(
            CommentLike.user_id == user_id,
            CommentLike.is_active == True
        ).all()
        return [like.comment_id for like in likes]

    @staticmethod
    def get_users_who_liked(db: Session, auth_db: Session, comment_id: int, limit: int = 10, offset: int = 0):
        """Retorna lista de usuários que curtiram um comentário, com paginação.
        Retorna apenas id, name e profile_photo dos usuários, ordenados por data de curtida (mais recentes primeiro)."""
        from app.domain.auth.models.user_model import User
        
        # Busca os user_ids que curtiram o comentário, ordenados por data de curtida (mais recentes primeiro)
        # Apenas likes ativos
        liked_user_ids_result = db.query(CommentLike.user_id).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.is_active == True
        ).order_by(CommentLike.created_at.desc()).offset(offset).limit(limit).all()
        
        if not liked_user_ids_result:
            return []
        
        # Extrai os IDs mantendo a ordem
        user_ids = [row[0] for row in liked_user_ids_result]
        
        # Busca os dados dos usuários
        users_query = auth_db.query(User.id, User.name, User.profile_photo).filter(
            User.id.in_(user_ids)
        ).all()
        
        # Cria um dicionário para acesso rápido por ID
        users_dict = {user.id: user for user in users_query}
        
        # Retorna como lista de dicionários mantendo a ordem original dos IDs
        return [
            {
                "id": user_id,
                "name": users_dict[user_id].name,
                "profile_photo": users_dict[user_id].profile_photo
            }
            for user_id in user_ids
            if user_id in users_dict
        ]

    @staticmethod
    def get_like_history(db: Session, comment_id: int, user_id: int):
        """Retorna o histórico completo de curtidas/descurtidas de um usuário para um comentário.
        Retorna lista ordenada por created_at (mais antigo primeiro)."""
        return db.query(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id
        ).order_by(CommentLike.created_at.asc()).all()

    @staticmethod
    def get_like_statistics(db: Session, comment_id: int, user_id: int):
        """Retorna estatísticas de curtidas de um usuário para um comentário:
        - total_likes: quantas vezes curtiu
        - total_unlikes: quantas vezes descurtiu
        - first_liked_at: quando curtiu pela primeira vez
        - last_liked_at: quando curtiu pela última vez
        - is_currently_liked: se está curtido no momento"""
        history = db.query(CommentLike).filter(
            CommentLike.comment_id == comment_id,
            CommentLike.user_id == user_id
        ).order_by(CommentLike.created_at.asc()).all()
        
        if not history:
            return {
                "total_likes": 0,
                "total_unlikes": 0,
                "first_liked_at": None,
                "last_liked_at": None,
                "is_currently_liked": False
            }
        
        # Total de vezes que curtiu = número total de registros criados
        total_likes = len(history)
        # Total de vezes que descurtiu = número de registros que foram desativados
        total_unlikes = len([h for h in history if not h.is_active and h.deactivated_at is not None])
        first_liked_at = history[0].created_at if history else None
        last_liked_at = history[-1].created_at if history else None
        is_currently_liked = any(h.is_active for h in history)
        
        return {
            "total_likes": total_likes,
            "total_unlikes": total_unlikes,
            "first_liked_at": first_liked_at.isoformat() if first_liked_at else None,
            "last_liked_at": last_liked_at.isoformat() if last_liked_at else None,
            "is_currently_liked": is_currently_liked
        }

