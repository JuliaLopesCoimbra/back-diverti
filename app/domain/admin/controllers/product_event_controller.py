# app/domain/admin/controllers/product_event_controller.py

from app.domain.admin.services.product_event_service import ProductEventService

class ProductEventController:

    @staticmethod
    def create(db, data, user, image_urls: list = None):
        return ProductEventService.create_product(db, data, user, image_urls)

    @staticmethod
    def list(db, event_id: int = None, limit: int = 50, offset: int = 0):
        return ProductEventService.list_products(db, event_id=event_id, limit=limit, offset=offset)

    @staticmethod
    def get(db, product_id: int):
        return ProductEventService.get_product(db, product_id)

    @staticmethod
    def get_by_event(db, event_id: int, limit: int = None, offset: int = 0):
        return ProductEventService.get_products_by_event(db, event_id, limit=limit, offset=offset)

    @staticmethod
    def update(db, product_id: int, data: dict, user, image_files: list = None, replace_images: bool = False):
        return ProductEventService.update_product(db, product_id, data, user, image_files, replace_images)

    @staticmethod
    def delete(db, product_id: int, user):
        return ProductEventService.delete_product(db, product_id, user)

