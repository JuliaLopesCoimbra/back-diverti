from sqlalchemy.orm import Session, joinedload
from app.domain.admin.models.news_model import NewsPost
from app.domain.admin.models.news_image_model import NewsImage
from sqlalchemy import desc, func

class NewsRepository:

    @staticmethod
    def create(db: Session, data: dict, image_urls: list = None):
        # Remove image_urls do data se existir (não é campo do modelo)
        news_data = {k: v for k, v in data.items() if k != 'image_urls'}
        news = NewsPost(**news_data)
        db.add(news)
        db.flush()  # Para obter o ID antes do commit
        
        # Cria as imagens associadas
        if image_urls:
            for index, image_url in enumerate(image_urls):
                news_image = NewsImage(
                    news_id=news.id,
                    image_url=image_url,
                    image_order=index
                )
                db.add(news_image)
        
        db.commit()
        db.refresh(news)
        return news

    @staticmethod
    def list_all(db: Session, limit: int = 10, offset: int = 0):
        return (
            db.query(NewsPost)
            .options(joinedload(NewsPost.images))
            .filter(NewsPost.status != "deleted", NewsPost.deleted_at.is_(None))
            .order_by(NewsPost.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get(db: Session, news_id: int, include_deleted: bool = False):
        query = (
            db.query(NewsPost)
            .options(joinedload(NewsPost.images))
            .filter(NewsPost.id == news_id)
        )
        if not include_deleted:
            query = query.filter(NewsPost.status != "deleted", NewsPost.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def delete(db: Session, news_id: int):
        """Método legado - não usar. Use NewsService.delete_post para soft delete."""
        # Este método não deve ser usado mais, mas mantido para compatibilidade
        post = db.query(NewsPost).filter(NewsPost.id == news_id).first()
        if post:
            db.delete(post)
            db.commit()
        return post

    @staticmethod
    def list_by_event(db, event_id: int, limit: int, offset: int):
        return (
            db.query(NewsPost)
            .options(joinedload(NewsPost.images))
            .filter(
                NewsPost.event_id == event_id,
                NewsPost.status != "deleted",
                NewsPost.deleted_at.is_(None)
            )
            .order_by(desc(NewsPost.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def list_by_author(db, author_id: int, event_id: int = None, limit: int = 10, offset: int = 0):
        """Lista posts do autor, incluindo aprovados, pendentes e rejeitados (exclui deletados), opcionalmente filtrado por evento"""
        query = (
            db.query(NewsPost)
            .options(joinedload(NewsPost.images))
            .filter(
                NewsPost.author_id == author_id,
                NewsPost.status.in_(["approved", "rejected", "pending"]),
                NewsPost.status != "deleted",
                NewsPost.deleted_at.is_(None)
            )
        )
        
        # Filtra por evento se fornecido
        if event_id is not None:
            query = query.filter(NewsPost.event_id == event_id)
        
        return (
            query
            .order_by(desc(NewsPost.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def list_pending_by_author(db, author_id: int, event_id: int = None, limit: int = 10, offset: int = 0):
        """Lista posts pendentes de um autor específico, opcionalmente filtrado por evento"""
        query = (
            db.query(NewsPost)
            .options(joinedload(NewsPost.images))
            .filter(
                NewsPost.author_id == author_id,
                NewsPost.status == "pending",
                NewsPost.status != "deleted",
                NewsPost.deleted_at.is_(None)
            )
        )
        
        # Filtra por evento se fornecido
        if event_id is not None:
            query = query.filter(NewsPost.event_id == event_id)
        
        return (
            query
            .order_by(desc(func.coalesce(NewsPost.updated_at, NewsPost.created_at)))
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def list_pending(db: Session, limit: int = 10, offset: int = 0, event_id: int = None):
        """Lista posts pendentes de aprovação, opcionalmente filtrados por evento"""
        query = (
            db.query(NewsPost)
            .options(joinedload(NewsPost.images))
            .filter(
                NewsPost.status == "pending",
                NewsPost.status != "deleted",
                NewsPost.deleted_at.is_(None)
            )
        )
        
        if event_id is not None:
            query = query.filter(NewsPost.event_id == event_id)
        
        return (
            query
            .order_by(desc(func.coalesce(NewsPost.updated_at, NewsPost.created_at)))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    @staticmethod
    def count_pending_by_event(db: Session, event_id: int) -> int:
        """Conta quantos posts pendentes existem para um evento"""
        return (
            db.query(NewsPost)
            .filter(
                NewsPost.event_id == event_id,
                NewsPost.status == "pending",
                NewsPost.status != "deleted",
                NewsPost.deleted_at.is_(None)
            )
            .count()
        )
    
    @staticmethod
    def approve_all_pending_by_event(db: Session, event_id: int, approver_id: int):
        """Aprova todos os posts pendentes de um evento"""
        from datetime import datetime
        posts = (
            db.query(NewsPost)
            .filter(
                NewsPost.event_id == event_id,
                NewsPost.status == "pending",
                NewsPost.status != "deleted",
                NewsPost.deleted_at.is_(None)
            )
            .all()
        )
        
        for post in posts:
            post.status = "approved"
            post.approved_by_id = approver_id
            post.approved_at = datetime.utcnow()
        
        db.commit()
        return len(posts)

    @staticmethod
    def list_approved(db: Session, limit: int = 10, offset: int = 0):
        """Lista apenas posts aprovados (exclui deletados)"""
        return (
            db.query(NewsPost)
            .options(joinedload(NewsPost.images))
            .filter(
                NewsPost.status == "approved",
                NewsPost.status != "deleted",
                NewsPost.deleted_at.is_(None)
            )
            .order_by(desc(NewsPost.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def list_approved_by_event(db: Session, event_id: int, limit: int = 10, offset: int = 0):
        """Lista posts aprovados de um evento específico, ordenados por approved_at (ou created_at como fallback)"""
        return (
            db.query(NewsPost)
            .options(joinedload(NewsPost.images))
            .filter(
                NewsPost.event_id == event_id,
                NewsPost.status == "approved",
                NewsPost.status != "deleted",
                NewsPost.deleted_at.is_(None)
            )
            .order_by(desc(func.coalesce(NewsPost.approved_at, NewsPost.created_at)))
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def list_rejected_by_rejector(db, rejector_id: int, event_id: int = None, limit: int = 10, offset: int = 0):
        """Lista posts rejeitados por um admin/subadmin específico, opcionalmente filtrado por evento"""
        query = (
            db.query(NewsPost)
            .options(joinedload(NewsPost.images))
            .filter(
                NewsPost.rejected_by_id == rejector_id,
                NewsPost.status == "rejected",
                NewsPost.status != "deleted",
                NewsPost.deleted_at.is_(None)
            )
        )
        
        # Filtra por evento se fornecido
        if event_id is not None:
            query = query.filter(NewsPost.event_id == event_id)
        
        return (
            query
            .order_by(desc(NewsPost.rejected_at))
            .limit(limit)
            .offset(offset)
            .all()
        )