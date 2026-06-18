# app/domain/admin/services/parade_lineup_item_service.py

from app.domain.admin.repositories.parade_lineup_item_repository import ParadeLineupItemRepository
from app.domain.admin.repositories.event_repository import EventRepository
from app.domain.admin.repositories.samba_school_repository import SambaSchoolRepository
from datetime import datetime

class ParadeLineupItemService:

    @staticmethod
    def create_parade_lineup_item(db, data: dict, user):
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem criar itens do lineup de desfile")

        # Verifica se o evento existe
        event = EventRepository.get_by_id(db, data['event_id'], force_db=True)
        if not event:
            raise ValueError("Evento não encontrado")

        # Verifica se a escola de samba existe
        samba_school = SambaSchoolRepository.get_by_id(db, data['samba_school_id'])
        if not samba_school:
            raise ValueError("Escola de samba não encontrada")
        
        if samba_school.event_id != data['event_id']:
            raise ValueError("A escola de samba não pertence a este evento")

        # Valida se já existe um item com a mesma ordem no mesmo evento
        if 'display_order' in data:
            existing_item = ParadeLineupItemRepository.get_by_event_id_and_order(
                db, data['event_id'], data['display_order']
            )
            if existing_item:
                raise ValueError(f"Já existe uma escola com a ordem {data['display_order']}. Cada escola deve ter uma ordem única.")

        # Adiciona campos de auditoria
        data['created_by_id'] = user.id

        return ParadeLineupItemRepository.create(db, data)

    @staticmethod
    def get_parade_lineup_items_by_event(db, event_id: int):
        """Busca todos os itens do lineup de desfile de um evento"""
        items = ParadeLineupItemRepository.get_by_event_id(db, event_id)
        # Adiciona informações da escola de samba
        result = []
        for item in items:
            item_dict = {
                "id": item.id,
                "event_id": item.event_id,
                "samba_school_id": item.samba_school_id,
                "performance_time": item.performance_time,
                "performance_end_time": item.performance_end_time,
                "event_date": item.event_date,
                "display_order": item.display_order,
                "description": item.description,
                "created_at": item.created_at,
                "created_by_id": item.created_by_id,
                "updated_at": item.updated_at,
                "updated_by_id": item.updated_by_id,
                "deleted_at": item.deleted_at,
                "deleted_by_id": item.deleted_by_id,
            }
            if item.samba_school:
                item_dict["samba_school_name"] = item.samba_school.name
                item_dict["samba_school_image_url"] = item.samba_school.image_url
            result.append(item_dict)
        return result

    @staticmethod
    def get_parade_lineup_item_by_id(db, parade_lineup_item_id: int):
        """Busca um item do lineup de desfile por ID"""
        item = ParadeLineupItemRepository.get_by_id(db, parade_lineup_item_id)
        if not item:
            return None
        
        item_dict = {
            "id": item.id,
            "event_id": item.event_id,
            "samba_school_id": item.samba_school_id,
            "performance_time": item.performance_time,
            "performance_end_time": item.performance_end_time,
            "event_date": item.event_date,
            "display_order": item.display_order,
            "description": item.description,
            "created_at": item.created_at,
            "created_by_id": item.created_by_id,
            "updated_at": item.updated_at,
            "updated_by_id": item.updated_by_id,
            "deleted_at": item.deleted_at,
            "deleted_by_id": item.deleted_by_id,
        }
        if item.samba_school:
            item_dict["samba_school_name"] = item.samba_school.name
            item_dict["samba_school_image_url"] = item.samba_school.image_url
        return item_dict

    @staticmethod
    def update_parade_lineup_item(db, parade_lineup_item_id: int, data: dict, user):
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem editar itens do lineup de desfile")

        parade_lineup_item = ParadeLineupItemRepository.get_by_id(db, parade_lineup_item_id)
        if not parade_lineup_item:
            raise ValueError("Item do lineup de desfile não encontrado")

        # Verifica se a escola de samba existe (se fornecida)
        if 'samba_school_id' in data and data['samba_school_id'] is not None:
            samba_school = SambaSchoolRepository.get_by_id(db, data['samba_school_id'])
            if not samba_school:
                raise ValueError("Escola de samba não encontrada")
            if samba_school.event_id != parade_lineup_item.event_id:
                raise ValueError("A escola de samba não pertence a este evento")

        # Valida se já existe outro item com a mesma ordem no mesmo evento
        if 'display_order' in data and data['display_order'] is not None:
            existing_item = ParadeLineupItemRepository.get_by_event_id_and_order(
                db, parade_lineup_item.event_id, data['display_order'], exclude_id=parade_lineup_item_id
            )
            if existing_item:
                raise ValueError(f"Já existe uma escola com a ordem {data['display_order']}. Cada escola deve ter uma ordem única.")

        # Adiciona campos de auditoria
        data['updated_by_id'] = user.id

        return ParadeLineupItemRepository.update(db, parade_lineup_item, data)

    @staticmethod
    def delete_parade_lineup_item(db, parade_lineup_item_id: int, user):
        if user.role not in ["admin_master", "admin"]:
            raise PermissionError("Apenas admin master ou admin podem deletar itens do lineup de desfile")

        parade_lineup_item = ParadeLineupItemRepository.get_by_id(db, parade_lineup_item_id)
        if not parade_lineup_item:
            raise ValueError("Item do lineup de desfile não encontrado")

        ParadeLineupItemRepository.soft_delete(db, parade_lineup_item, user.id)
        return True




