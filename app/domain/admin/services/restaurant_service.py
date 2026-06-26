from sqlalchemy.orm import Session

from app.domain.admin.repositories.menu_item_repository import MenuItemRepository
from app.domain.admin.repositories.restaurant_repository import RestaurantRepository
from app.domain.admin.schemas.menu_item_schema import MenuItemCreateSchema, MenuItemUpdateSchema
from app.domain.admin.schemas.restaurant_schema import RestaurantCreateSchema, RestaurantUpdateSchema


class RestaurantService:
    @staticmethod
    def create(db: Session, data: RestaurantCreateSchema, admin_id: int):
        return RestaurantRepository.create(db, {**data.model_dump(), "created_by_id": admin_id})

    @staticmethod
    def get_by_event(db: Session, event_id: int, active_only: bool = False):
        return RestaurantRepository.get_by_event(db, event_id, active_only=active_only)

    @staticmethod
    def get_by_id(db: Session, restaurant_id: int):
        obj = RestaurantRepository.get(db, restaurant_id)
        if not obj:
            raise ValueError("Restaurante não encontrado")
        return obj

    @staticmethod
    def update(db: Session, restaurant_id: int, data: RestaurantUpdateSchema, admin_id: int):
        obj = RestaurantService.get_by_id(db, restaurant_id)
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
        updates["updated_by_id"] = admin_id
        return RestaurantRepository.update(db, obj, updates)

    @staticmethod
    def delete(db: Session, restaurant_id: int, admin_id: int):
        obj = RestaurantService.get_by_id(db, restaurant_id)
        RestaurantRepository.soft_delete(db, obj, admin_id)

    # ── Menu items ────────────────────────────────────────────────────────────

    @staticmethod
    def create_item(db: Session, data: MenuItemCreateSchema, admin_id: int):
        RestaurantService.get_by_id(db, data.restaurant_id)
        return MenuItemRepository.create(db, {**data.model_dump(), "created_by_id": admin_id})

    @staticmethod
    def get_items(db: Session, restaurant_id: int, available_only: bool = False):
        return MenuItemRepository.get_by_restaurant(db, restaurant_id, available_only=available_only)

    @staticmethod
    def update_item(db: Session, item_id: int, data: MenuItemUpdateSchema, admin_id: int):
        obj = MenuItemRepository.get(db, item_id)
        if not obj:
            raise ValueError("Item não encontrado")
        updates = {k: v for k, v in data.model_dump(exclude_unset=True).items()}
        updates["updated_by_id"] = admin_id
        return MenuItemRepository.update(db, obj, updates)

    @staticmethod
    def delete_item(db: Session, item_id: int, admin_id: int):
        obj = MenuItemRepository.get(db, item_id)
        if not obj:
            raise ValueError("Item não encontrado")
        MenuItemRepository.soft_delete(db, obj, admin_id)
