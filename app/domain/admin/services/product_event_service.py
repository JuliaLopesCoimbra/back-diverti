# app/domain/admin/services/product_event_service.py

from app.domain.admin.repositories.product_event_repository import ProductEventRepository
from app.domain.admin.repositories.event_repository import EventRepository

class ProductEventService:

    @staticmethod
    def create_product(db, data, user, image_urls: list = None):
        """Cria um novo produto de evento"""
        # Valida se o evento existe
        event = EventRepository.get_by_id(db, data["event_id"], force_db=True)
        if not event:
            raise ValueError("Evento não encontrado")
        
        # Adiciona created_by_id
        data["created_by_id"] = user.id
        
        product = ProductEventRepository.create(db, data, image_urls)
        return product

    @staticmethod
    def list_products(db, event_id: int = None, limit: int = 50, offset: int = 0):
        """Lista produtos, opcionalmente filtrados por evento"""
        return ProductEventRepository.list_all(db, event_id=event_id, limit=limit, offset=offset)

    @staticmethod
    def get_product(db, product_id: int):
        """Busca um produto por ID"""
        product = ProductEventRepository.get(db, product_id)
        if not product:
            raise ValueError("Produto não encontrado")
        return product

    @staticmethod
    def get_products_by_event(db, event_id: int, limit: int = None, offset: int = 0):
        """Busca produtos de um evento com paginação opcional"""
        # Valida se o evento existe
        event = EventRepository.get_by_id(db, event_id, force_db=True)
        if not event:
            raise ValueError("Evento não encontrado")
        
        return ProductEventRepository.get_by_event(db, event_id, limit=limit, offset=offset)

    @staticmethod
    def update_product(db, product_id: int, data: dict, user, image_files: list = None, replace_images: bool = False):
        """Atualiza um produto"""
        product = ProductEventRepository.get(db, product_id, include_deleted=False)
        if not product:
            raise ValueError("Produto não encontrado")
        
        # Se está atualizando o event_id, valida se o evento existe
        if "event_id" in data and data["event_id"]:
            event = EventRepository.get_by_id(db, data["event_id"], force_db=True)
            if not event:
                raise ValueError("Evento não encontrado")
        
        # Adiciona updated_by_id
        data["updated_by_id"] = user.id
        
        # Remove image_urls do data se existir
        image_urls = None
        if image_files:
            from app.infra.s3_upload import upload_product_images_to_s3
            image_urls = upload_product_images_to_s3(image_files, product_id, folder="product_photos")
            
            if replace_images:
                # Remove todas as imagens antigas
                ProductEventRepository.delete_images(db, product_id)
                # Adiciona as novas
                if image_urls:
                    ProductEventRepository.add_images(db, product_id, image_urls)
            else:
                # Adiciona às existentes
                if image_urls:
                    ProductEventRepository.add_images(db, product_id, image_urls)
        
        # Se há IDs de imagens para remover (quando usuário remove imagens existentes individualmente)
        # Só processa se não estiver substituindo todas as imagens
        if not replace_images and "removed_image_ids" in data and data["removed_image_ids"]:
            ProductEventRepository.delete_images_by_ids(db, data["removed_image_ids"])
            # Remove do data para não tentar atualizar no modelo
            del data["removed_image_ids"]
        
        # Remove campos que não são do modelo
        update_data = {k: v for k, v in data.items() if k not in ['image_urls', 'image_files']}
        
        result = ProductEventRepository.update(db, product, update_data)
        return result

    @staticmethod
    def delete_product(db, product_id: int, user):
        """Soft delete de um produto"""
        product = ProductEventRepository.get(db, product_id, include_deleted=False)
        if not product:
            raise ValueError("Produto não encontrado")
        
        return ProductEventRepository.soft_delete(db, product, user.id)

