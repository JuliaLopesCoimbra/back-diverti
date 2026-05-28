# app/domain/admin/repositories/lineup_item_repository.py

from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.domain.admin.models.lineup_item_model import LineupItem
from app.infra.redis import redis_client, CacheKeys

class LineupItemRepository:

    @staticmethod
    def create(db: Session, data: dict, created_by_id: int = None):
        if created_by_id:
            data['created_by_id'] = created_by_id
        
        lineup_item = LineupItem(**data)
        db.add(lineup_item)
        db.commit()
        db.refresh(lineup_item)
        
        # Invalida cache do evento
        if 'event_id' in data:
            redis_client.delete(CacheKeys.event_details(data['event_id']))
        
        return lineup_item

    @staticmethod
    def get_by_id(db: Session, lineup_item_id: int, include_deleted: bool = False):
        query = db.query(LineupItem).filter(LineupItem.id == lineup_item_id)
        if not include_deleted:
            query = query.filter(LineupItem.deleted_at.is_(None))
        return query.first()

    @staticmethod
    def get_by_event_id(db: Session, event_id: int, include_deleted: bool = False):
        """Busca todos os itens do lineup de um evento ordenados por display_order e performance_time"""
        query = db.query(LineupItem).filter(LineupItem.event_id == event_id)
        if not include_deleted:
            query = query.filter(LineupItem.deleted_at.is_(None))
        return query.order_by(
            LineupItem.event_date.asc().nullsfirst(),
            LineupItem.display_order.asc(),
            LineupItem.performance_time.asc()
        ).all()

    @staticmethod
    def get_by_event_id_and_date(db: Session, event_id: int, event_date = None, include_deleted: bool = False):
        """Busca itens do lineup de um evento filtrando por data"""
        query = db.query(LineupItem).filter(LineupItem.event_id == event_id)
        if event_date is None:
            query = query.filter(LineupItem.event_date.is_(None))
        else:
            query = query.filter(LineupItem.event_date == event_date)
        if not include_deleted:
            query = query.filter(LineupItem.deleted_at.is_(None))
        return query.order_by(
            LineupItem.display_order.asc(),
            LineupItem.performance_time.asc()
        ).all()

    @staticmethod
    def get_by_event_id_and_order(db: Session, event_id: int, display_order: int, event_date = None, exclude_id: int = None, include_deleted: bool = False):
        """Busca um item do lineup por evento, data e ordem"""
        query = db.query(LineupItem).filter(
            and_(
                LineupItem.event_id == event_id,
                LineupItem.display_order == display_order
            )
        )
        if event_date is None:
            query = query.filter(LineupItem.event_date.is_(None))
        else:
            query = query.filter(LineupItem.event_date == event_date)
        if not include_deleted:
            query = query.filter(LineupItem.deleted_at.is_(None))
        if exclude_id:
            query = query.filter(LineupItem.id != exclude_id)
        return query.first()

    @staticmethod
    def update(db: Session, lineup_item: LineupItem, data: dict, updated_by_id: int = None):
        for key, value in data.items():
            if value is not None:
                setattr(lineup_item, key, value)
        
        if updated_by_id:
            lineup_item.updated_by_id = updated_by_id

        db.commit()
        db.refresh(lineup_item)
        
        # Invalida cache do evento
        if lineup_item.event_id:
            redis_client.delete(CacheKeys.event_details(lineup_item.event_id))
        
        return lineup_item

    @staticmethod
    def bulk_update_orders(
        db: Session,
        event_id: int,
        item_orders: list[tuple[int, int]],
        event_date = None,
        updated_by_id: int = None
    ):
        item_ids = [item_id for item_id, _ in item_orders]
        query = db.query(LineupItem).filter(
            LineupItem.event_id == event_id,
            LineupItem.id.in_(item_ids),
            LineupItem.deleted_at.is_(None),
        )
        if event_date is None:
            query = query.filter(LineupItem.event_date.is_(None))
        else:
            query = query.filter(LineupItem.event_date == event_date)

        items = query.all()
        items_by_id = {item.id: item for item in items}

        for item_id, display_order in item_orders:
            lineup_item = items_by_id.get(item_id)
            if lineup_item is None:
                raise ValueError("Um ou mais artistas nao pertencem ao evento/data informados")
            lineup_item.display_order = display_order
            if updated_by_id:
                lineup_item.updated_by_id = updated_by_id

        db.commit()

        redis_client.delete(CacheKeys.event_details(event_id))
        return items

    @staticmethod
    def delete(db: Session, lineup_item: LineupItem, deleted_by_id: int = None):
        """Soft delete - marca como deletado em vez de deletar fisicamente"""
        from datetime import datetime, timezone
        
        lineup_item.deleted_at = datetime.now(timezone.utc)
        if deleted_by_id:
            lineup_item.deleted_by_id = deleted_by_id
        
        event_id = lineup_item.event_id
        db.commit()
        db.refresh(lineup_item)
        
        # Invalida cache do evento
        if event_id:
            redis_client.delete(CacheKeys.event_details(event_id))

