# app/domain/interactions/repositories/comment_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone
from app.domain.users.models.comment_model import Comment

class CommentRepository:

    @staticmethod
    def create(db: Session, content: str, news_id: int, user_id: int, parent_comment_id: int = None, admin_db: Session = None):
        # Busca o event_id da notícia se admin_db foi fornecido
        event_id = None
        if admin_db is not None:
            from app.domain.admin.models.news_model import NewsPost
            news = admin_db.query(NewsPost.event_id).filter(NewsPost.id == news_id).first()
            if news:
                event_id = news[0]
        
        comment = Comment(
            content=content,
            news_id=news_id,
            user_id=user_id,
            parent_comment_id=parent_comment_id,
            event_id=event_id
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def list_all(db: Session, news_id: int, parent_comment_id: int = None, limit: int = 50, offset: int = 0):
        """
        Lista comentários com paginação obrigatória
        
        Args:
            db: Sessão do banco de dados
            news_id: ID da notícia
            parent_comment_id: ID do comentário pai (None para comentários principais)
            limit: Número máximo de comentários (padrão: 50, máximo: 100)
            offset: Número de comentários para pular
        
        Returns:
            Lista de comentários paginados
        """
        # Limita o máximo de comentários por requisição para evitar sobrecarga
        limit = min(limit, 100)  # Máximo de 100 comentários por requisição
        
        query = db.query(Comment).filter(
            Comment.news_id == news_id,
            Comment.deleted_at.is_(None)  # Filtra apenas comentários não deletados
        )
        
        # Se parent_comment_id for None, retorna apenas comentários principais
        # Se fornecido, retorna respostas daquele comentário
        if parent_comment_id is None:
            query = query.filter(Comment.parent_comment_id.is_(None))
            # Comentários principais: do mais recente ao mais antigo (DESC)
            return query.order_by(desc(Comment.created_at), desc(Comment.id)).limit(limit).offset(offset).all()
        else:
            query = query.filter(Comment.parent_comment_id == parent_comment_id)
            # Subcomentários (respostas): do mais antigo ao mais recente (ASC)
            return query.order_by(Comment.created_at, Comment.id).limit(limit).offset(offset).all()
    
    @staticmethod
    def count_replies(db: Session, comment_id: int) -> int:
        """Conta o número de respostas não deletadas de um comentário"""
        return db.query(Comment).filter(
            Comment.parent_comment_id == comment_id,
            Comment.deleted_at.is_(None)
        ).count()
    
    @staticmethod
    def count_main_comments(db: Session, news_id: int, auth_db=None) -> int:
        """
        Conta o número total de comentários principais (não deletados) de uma notícia.
        Se auth_db for fornecido, conta apenas comentários de usuários que ainda existem.
        """
        # Busca todos os comentários principais não deletados
        comments = db.query(Comment.user_id).filter(
            Comment.news_id == news_id,
            Comment.parent_comment_id.is_(None),
            Comment.deleted_at.is_(None)
        ).all()
        
        if not comments:
            return 0
        
        # Se auth_db foi fornecido, verifica quais usuários ainda existem
        if auth_db is not None:
            from app.domain.auth.models.user_model import User
            # Extrai os user_ids únicos
            user_ids = list(set([comment[0] for comment in comments]))
            # Verifica quais usuários existem
            existing_users = auth_db.query(User.id).filter(User.id.in_(user_ids)).all()
            existing_user_ids = set([user[0] for user in existing_users])
            # Conta apenas comentários de usuários que existem
            return sum(1 for comment in comments if comment[0] in existing_user_ids)
        
        # Se auth_db não foi fornecido, retorna a contagem total (comportamento antigo)
        return len(comments)
    
    @staticmethod
    def get_by_id(db: Session, comment_id: int):
        """Busca um comentário por ID (incluindo deletados)"""
        return db.query(Comment).filter(Comment.id == comment_id).first()
    
    @staticmethod
    def soft_delete(db: Session, comment_id: int, deleted_by_user_id: int = None):
        """Soft delete de um comentário - marca como deletado"""
        comment = CommentRepository.get_by_id(db, comment_id)
        if comment:
            comment.deleted_at = datetime.now(timezone.utc)
            comment.deleted_by_user_id = deleted_by_user_id
            db.commit()
            db.refresh(comment)
        return comment
    
    @staticmethod
    def soft_delete_cascade(db: Session, comment_id: int, deleted_by_user_id: int = None):
        """
        Soft delete em cascata - deleta o comentário e todas suas respostas.
        Otimizado para evitar recursão: busca todos os descendentes iterativamente
        e marca todos como deletados em uma única operação.
        """
        # Coleta todos os IDs de comentários a deletar (incluindo descendentes)
        comment_ids_to_delete = [comment_id]
        deleted_at = datetime.now(timezone.utc)
        
        # Busca iterativamente todos os descendentes
        # Evita recursão e múltiplas queries desnecessárias
        current_level = [comment_id]
        
        while current_level:
            # Busca todos os filhos diretos dos comentários do nível atual
            next_level = db.query(Comment.id).filter(
                Comment.parent_comment_id.in_(current_level),
                Comment.deleted_at.is_(None)
            ).all()
            
            # Extrai os IDs das tuplas
            next_level_ids = [row[0] for row in next_level]
            
            if not next_level_ids:
                break  # Não há mais descendentes
            
            # Adiciona à lista de IDs a deletar
            comment_ids_to_delete.extend(next_level_ids)
            current_level = next_level_ids
        
        # Marca todos os comentários como deletados em uma única operação
        # Muito mais eficiente que múltiplas atualizações individuais
        db.query(Comment).filter(
            Comment.id.in_(comment_ids_to_delete),
            Comment.deleted_at.is_(None)  # Apenas os que ainda não foram deletados
        ).update({
            'deleted_at': deleted_at,
            'deleted_by_user_id': deleted_by_user_id
        }, synchronize_session=False)
        
        db.commit()
        
        # Retorna o comentário principal deletado
        return CommentRepository.get_by_id(db, comment_id)
