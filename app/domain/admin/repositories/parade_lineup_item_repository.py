# app/domain/admin/repositories/parade_lineup_item_repository.py

from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.domain.admin.models.parade_lineup_item_model import ParadeLineupItem
from app.infra.redis import redis_client, CacheKeys

class ParadeLineupItemRepository:

    @staticmethod
    def create(db: Session, data: dict):
        parade_lineup_item = ParadeLineupItem(**data)
        db.add(parade_lineup_item)
        db.commit()
        db.refresh(parade_lineup_item)
        
        # Invalida cache do evento
        if 'event_id' in data:
            redis_client.delete(CacheKeys.event_details(data['event_id']))
        
        return parade_lineup_item

    @staticmethod
    def get_by_id(db: Session, parade_lineup_item_id: int, include_deleted: bool = False):
        query = db.query(ParadeLineupItem).filter(ParadeLineupItem.id == parade_lineup_item_id)
        if not include_deleted:
            query = query.filter(ParadeLineupItem.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_event_id(db: Session, event_id: int, include_deleted: bool = False):
        """Busca todos os itens do lineup de desfile de um evento ordenados por display_order e performance_time"""
        query = db.query(ParadeLineupItem).filter(ParadeLineupItem.event_id == event_id)
        if not include_deleted:
            query = query.filter(ParadeLineupItem.deleted_at.is_(None))
        return query.order_by(
            ParadeLineupItem.display_order.asc(),
            ParadeLineupItem.performance_time.asc()
        ).all()

    @staticmethod
    def get_by_event_id_and_order(db: Session, event_id: int, display_order: int, exclude_id: int = None, include_deleted: bool = False):
        """Busca um item do lineup por evento e ordem (para validação de ordem única)"""
        query = db.query(ParadeLineupItem).filter(
            and_(
                ParadeLineupItem.event_id == event_id,
                ParadeLineupItem.display_order == display_order
            )
        )
        if not include_deleted:
            query = query.filter(ParadeLineupItem.deleted_at.is_(None))
        if exclude_id:
            query = query.filter(ParadeLineupItem.id != exclude_id)
        return query.first()

    @staticmethod
    def update(db: Session, parade_lineup_item: ParadeLineupItem, data: dict):
        for key, value in data.items():
            if value is not None:
                setattr(parade_lineup_item, key, value)

        db.commit()
        db.refresh(parade_lineup_item)
        
        # Invalida cache do evento
        if parade_lineup_item.event_id:
            redis_client.delete(CacheKeys.event_details(parade_lineup_item.event_id))
        
        return parade_lineup_item

    @staticmethod
    def soft_delete(db: Session, parade_lineup_item: ParadeLineupItem, deleted_by_id: int):
        """Soft delete do item"""
        from datetime import datetime
        parade_lineup_item.deleted_at = datetime.utcnow()
        parade_lineup_item.deleted_by_id = deleted_by_id
        db.commit()
        db.refresh(parade_lineup_item)
        
        # Invalida cache do evento
        if parade_lineup_item.event_id:
            redis_client.delete(CacheKeys.event_details(parade_lineup_item.event_id))
        
        return parade_lineup_item




