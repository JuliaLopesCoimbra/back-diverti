# app/domain/admin/repositories/product_event_repository.py

from sqlalchemy.orm import Session, joinedload
from app.domain.admin.models.product_event_model import ProductEvent
from app.domain.admin.models.product_event_image_model import ProductEventImage
from sqlalchemy import desc

class ProductEventRepository:

    @staticmethod
    def create(db: Session, data: dict, image_urls: list = None):
        # Remove image_urls do data se existir (não é campo do modelo)
        product_data = {k: v for k, v in data.items() if k != 'image_urls'}
        product = ProductEvent(**product_data)
        db.add(product)
        db.flush()  # Para obter o ID antes do commit
        
        # Cria as imagens associadas
        if image_urls:
            for index, image_url in enumerate(image_urls):
                product_image = ProductEventImage(
                    product_id=product.id,
                    image_url=image_url,
                    image_order=index
                )
                db.add(product_image)
        
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def list_all(db: Session, event_id: int = None, limit: int = 50, offset: int = 0):
        query = db.query(ProductEvent).options(joinedload(ProductEvent.images))
        
        # Filtra por evento se fornecido
        if event_id:
            query = query.filter(ProductEvent.event_id == event_id)
        
        # Filtra apenas produtos não deletados
        query = query.filter(
            ProductEvent.status != "deleted",
            ProductEvent.deleted_at.is_(None)
        )
        
        return query.order_by(ProductEvent.created_at.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def get(db: Session, product_id: int, include_deleted: bool = False):
        query = (
            db.query(ProductEvent)
            .options(joinedload(ProductEvent.images))
            .filter(ProductEvent.id == product_id)
        )
        if not include_deleted:
            query = query.filter(
                ProductEvent.status != "deleted",
                ProductEvent.deleted_at.is_(None)
            )
        return query.first()

    @staticmethod
    def get_by_event(db: Session, event_id: int, limit: int = None, offset: int = 0, include_deleted: bool = False):
        query = (
            db.query(ProductEvent)
            .options(joinedload(ProductEvent.images))
            .filter(ProductEvent.event_id == event_id)
        )
        if not include_deleted:
            query = query.filter(
                ProductEvent.status != "deleted",
                ProductEvent.deleted_at.is_(None)
            )
        query = query.order_by(ProductEvent.created_at.desc())
        
        if limit is not None:
            query = query.offset(offset).limit(limit)
        
        return query.all()

    @staticmethod
    def update(db: Session, product: ProductEvent, data: dict):
        for key, value in data.items():
            if value is not None:
                setattr(product, key, value)
        
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete_images(db: Session, product_id: int):
        """Remove todas as imagens de um produto"""
        db.query(ProductEventImage).filter(
            ProductEventImage.product_id == product_id
        ).delete()
        db.commit()

    @staticmethod
    def delete_images_by_ids(db: Session, image_ids: list):
        """Remove imagens específicas por seus IDs"""
        if image_ids:
            db.query(ProductEventImage).filter(
                ProductEventImage.id.in_(image_ids)
            ).delete(synchronize_session=False)
            db.commit()

    @staticmethod
    def add_images(db: Session, product_id: int, image_urls: list):
        """Adiciona novas imagens a um produto"""
        # Pega a ordem máxima atual
        max_order = db.query(ProductEventImage.image_order).filter(
            ProductEventImage.product_id == product_id
        ).order_by(desc(ProductEventImage.image_order)).first()
        
        start_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0
        
        for index, image_url in enumerate(image_urls):
            product_image = ProductEventImage(
                product_id=product_id,
                image_url=image_url,
                image_order=start_order + index
            )
            db.add(product_image)
        
        db.commit()

    @staticmethod
    def soft_delete(db: Session, product: ProductEvent, deleted_by_id: int):
        """Soft delete do produto"""
        from datetime import datetime
        product.status = "deleted"
        product.deleted_at = datetime.utcnow()
        product.deleted_by_id = deleted_by_id
        db.commit()
        db.refresh(product)
        return product

