# app/domain/interactions/repositories/like_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from app.domain.users.models.like_model import Like

class LikeRepository:

    @staticmethod
    def get_like(db: Session, news_id: int, user_id: int):
        """Retorna o like ativo (is_active=True) para um usuário e notícia"""
        return db.query(Like).filter(
            Like.news_id == news_id,
            Like.user_id == user_id,
            Like.is_active == True
        ).first()

    @staticmethod
    def create(db: Session, news_id: int, user_id: int, ip_address: str = None, user_agent: str = None, admin_db: Session = None):
        """Sempre cria um NOVO registro de like para manter histórico completo.
        Se já existe um like ativo, retorna ele (evita duplicatas simultâneas).
        Caso contrário, cria um novo registro com timestamp atual."""
        # Verifica se já existe um like ativo (evita duplicatas em race conditions)
        existing_like = db.query(Like).filter(
            Like.news_id == news_id,
            Like.user_id == user_id,
            Like.is_active == True
        ).first()
        
        if existing_like:
            # Se já existe um like ativo, retorna ele (não cria duplicado simultâneo)
            # Isso evita problemas de race condition, mas mantém o histórico anterior
            return existing_like
        
        # Busca o event_id da notícia se admin_db foi fornecido
        event_id = None
        if admin_db is not None:
            from app.domain.admin.models.news_model import NewsPost
            news = admin_db.query(NewsPost.event_id).filter(NewsPost.id == news_id).first()
            if news:
                event_id = news[0]
        
        # Sempre cria um NOVO registro para manter histórico completo
        # Mesmo que tenha existido um like antes, criamos um novo com novo timestamp
        like = Like(
            news_id=news_id,
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
    def remove(db: Session, news_id: int, user_id: int):
        """Marca o like mais recente como inativo (soft delete) em vez de deletar fisicamente.
        Isso preserva o histórico completo de todas as curtidas/descurtidas."""
        # Busca o like ativo mais recente (ordenado por created_at desc)
        like = db.query(Like).filter(
            Like.news_id == news_id,
            Like.user_id == user_id,
            Like.is_active == True
        ).order_by(Like.created_at.desc()).first()
        
        if like:
            like.is_active = False
            like.deactivated_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False

    @staticmethod
    def count_by_news(db: Session, news_id: int) -> int:
        """Conta apenas likes ativos"""
        return db.query(Like).filter(
            Like.news_id == news_id,
            Like.is_active == True
        ).count()

    @staticmethod
    def get_liked_news_ids(db: Session, user_id: int, event_id: int = None, admin_db: Session = None):
        """Retorna lista de news_id que o usuário curtiu, opcionalmente filtrado por evento.
        Apenas posts com status 'approved' são retornados.
        Otimizado para não carregar objetos completos na memória - busca apenas os IDs."""
        
        # Sempre precisa do admin_db para filtrar por status approved
        if admin_db is None:
            return []
        
        # Busca apenas os news_id (não objetos completos Like) - muito mais eficiente em memória
        # Retorna tuplas (news_id,) em vez de objetos Like completos
        # Apenas likes ativos
        liked_news_ids_result = db.query(Like.news_id).filter(
            Like.user_id == user_id,
            Like.is_active == True
        ).all()
        
        if not liked_news_ids_result:
            return []
        
        # Extrai apenas os IDs das tuplas (mais eficiente que carregar objetos completos)
        liked_news_ids = [row[0] for row in liked_news_ids_result]
        
        # Converte para tupla (mais eficiente que lista para IN queries em alguns bancos)
        liked_news_ids_tuple = tuple(liked_news_ids)
        
        from app.domain.admin.models.news_model import NewsPost
        
        # Filtra apenas posts aprovados e não deletados
        query = admin_db.query(NewsPost.id).filter(
            NewsPost.id.in_(liked_news_ids_tuple),
            NewsPost.status == "approved",
            NewsPost.status != "deleted",
            NewsPost.deleted_at.is_(None)
        )
        
        # Se tiver event_id, também filtra por evento
        if event_id is not None:
            query = query.filter(NewsPost.event_id == event_id)
        
        # Retorna apenas os IDs, sem carregar objetos completos
        news_results = query.all()
        
        # Extrai apenas os IDs das tuplas
        return [row[0] for row in news_results]

    @staticmethod
    def get_users_who_liked(db: Session, auth_db: Session, news_id: int, limit: int = 10, offset: int = 0):
        """Retorna lista de usuários que curtiram uma notícia, com paginação.
        Retorna apenas id, name e profile_photo dos usuários, ordenados por data de curtida (mais recentes primeiro)."""
        from app.domain.auth.models.user_model import User
        
        # Busca os user_ids que curtiram a notícia, ordenados por data de curtida (mais recentes primeiro)
        # Apenas likes ativos
        liked_user_ids_result = db.query(Like.user_id).filter(
            Like.news_id == news_id,
            Like.is_active == True
        ).order_by(Like.created_at.desc()).offset(offset).limit(limit).all()
        
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
    def get_like_history(db: Session, news_id: int, user_id: int):
        """Retorna o histórico completo de curtidas/descurtidas de um usuário para uma notícia.
        Retorna lista ordenada por created_at (mais antigo primeiro)."""
        return db.query(Like).filter(
            Like.news_id == news_id,
            Like.user_id == user_id
        ).order_by(Like.created_at.asc()).all()

    @staticmethod
    def get_like_statistics(db: Session, news_id: int, user_id: int):
        """Retorna estatísticas de curtidas de um usuário para uma notícia:
        - total_likes: quantas vezes curtiu
        - total_unlikes: quantas vezes descurtiu
        - first_liked_at: quando curtiu pela primeira vez
        - last_liked_at: quando curtiu pela última vez
        - is_currently_liked: se está curtido no momento"""
        history = db.query(Like).filter(
            Like.news_id == news_id,
            Like.user_id == user_id
        ).order_by(Like.created_at.asc()).all()
        
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