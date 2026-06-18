# app/domain/admin/services/lineup_item_service.py

from app.domain.admin.repositories.lineup_item_repository import LineupItemRepository
from app.domain.admin.repositories.event_repository import EventRepository

class LineupItemService:

    @staticmethod
    def create_lineup_item(db, data: dict, user):
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem criar itens do lineup")

        # Verifica se o evento existe
        event = EventRepository.get_by_id(db, data['event_id'], force_db=True)
        if not event:
            raise ValueError("Evento não encontrado")

        if data.get('display_order') is None:
            same_day_items = LineupItemRepository.get_by_event_id_and_date(
                db,
                data['event_id'],
                data.get('event_date')
            )
            data['display_order'] = len(same_day_items)

        # Valida se já existe um item com a mesma ordem no mesmo evento e dia
        if 'display_order' in data and data['display_order'] is not None:
            existing_item = LineupItemRepository.get_by_event_id_and_order(
                db,
                data['event_id'],
                data['display_order'],
                data.get('event_date')
            )
            if existing_item:
                raise ValueError(f"Ja existe um artista com a ordem {data['display_order']} para este dia.")

        return LineupItemRepository.create(db, data, created_by_id=user.id)

    @staticmethod
    def get_lineup_items_by_event(db, event_id: int):
        """Busca todos os itens do lineup de um evento"""
        return LineupItemRepository.get_by_event_id(db, event_id)

    @staticmethod
    def get_lineup_item_by_id(db, lineup_item_id: int):
        """Busca um item do lineup por ID"""
        return LineupItemRepository.get_by_id(db, lineup_item_id)

    @staticmethod
    def update_lineup_item(db, lineup_item_id: int, data: dict, user):
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem editar itens do lineup")

        lineup_item = LineupItemRepository.get_by_id(db, lineup_item_id)
        if not lineup_item:
            raise ValueError("Item do lineup não encontrado")

        target_event_date = data['event_date'] if 'event_date' in data else lineup_item.event_date

        # Valida se já existe outro item com a mesma ordem no mesmo evento e dia
        if 'display_order' in data and data['display_order'] is not None:
            existing_item = LineupItemRepository.get_by_event_id_and_order(
                db,
                lineup_item.event_id,
                data['display_order'],
                target_event_date,
                exclude_id=lineup_item_id
            )
            if existing_item:
                raise ValueError(f"Ja existe um artista com a ordem {data['display_order']} para este dia.")

        return LineupItemRepository.update(db, lineup_item, data, updated_by_id=user.id)

    @staticmethod
    def reorder_lineup_items(db, event_id: int, event_date, item_ids: list[int], user):
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem reordenar itens do lineup")

        event = EventRepository.get_by_id(db, event_id, force_db=True)
        if not event:
            raise ValueError("Evento não encontrado")

        same_day_items = LineupItemRepository.get_by_event_id_and_date(db, event_id, event_date)
        same_day_ids = [item.id for item in same_day_items]

        if sorted(item_ids) != sorted(same_day_ids):
            raise ValueError("A nova ordem precisa conter todos os artistas do dia selecionado")

        item_orders = [(item_id, index) for index, item_id in enumerate(item_ids)]
        return LineupItemRepository.bulk_update_orders(
            db,
            event_id,
            item_orders,
            event_date=event_date,
            updated_by_id=user.id
        )

    @staticmethod
    def delete_lineup_item(db, lineup_item_id: int, user):
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem deletar itens do lineup")

        lineup_item = LineupItemRepository.get_by_id(db, lineup_item_id)
        if not lineup_item:
            raise ValueError("Item do lineup não encontrado")

        LineupItemRepository.delete(db, lineup_item, deleted_by_id=user.id)
        return True

