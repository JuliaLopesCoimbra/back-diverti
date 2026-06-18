# app/domain/admin/routes/product_event_routes.py

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, File, UploadFile
from sqlalchemy.orm import Session
from decimal import Decimal

from app.config.admin_db import get_admin_db
from app.domain.admin.controllers.product_event_controller import ProductEventController
from app.core.security.auth_dependency import get_current_user
from app.core.security.permissions import require_admin_or_master
from app.domain.auth.models.user_model import User
from app.domain.admin.schemas.product_event_schema import (
    ProductEventResponseSchema,
    ProductEventCreateSchema,
    ProductEventUpdateSchema
)
from app.infra.s3_upload import upload_product_images_to_s3

router = APIRouter(prefix="/admin", tags=["Admin - Product Events"])


@router.post(
    "/products-event",
    response_model=ProductEventResponseSchema,
    status_code=status.HTTP_201_CREATED
)
def create_product_event(
    name: str = Form(...),
    description: str = Form(None),
    price: str = Form(...),  # Recebe como string e converte para Decimal
    status: str = Form("active"),
    stock: int = Form(0),
    last_pieces: bool = Form(False),
    event_id: int = Form(...),
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master)
):
    """Cria um novo produto de evento"""
    try:
        # Converte price para Decimal
        price_decimal = Decimal(price)
        if price_decimal < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O preço não pode ser negativo"
            )
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preço inválido"
        )
    
    # Valida status
    if status not in ["active", "inactive"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status inválido. Use 'active' ou 'inactive'"
        )
    
    # Valida estoque
    if stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O estoque não pode ser negativo"
        )
    
    data = {
        "name": name,
        "description": description,
        "price": price_decimal,
        "status": status,
        "stock": stock,
        "last_pieces": last_pieces,
        "event_id": event_id
    }
    
    try:
        # Cria o produto primeiro (sem imagens)
        product = ProductEventController.create(db, data, user, image_urls=None)
        
        # Se há imagens, faz upload e adiciona ao produto
        if images:
            image_urls = upload_product_images_to_s3(images, product.id, folder="product_photos")
            # Adiciona as imagens ao produto
            from app.domain.admin.repositories.product_event_repository import ProductEventRepository
            ProductEventRepository.add_images(db, product.id, image_urls)
            # Recarrega o produto com as imagens
            db.refresh(product)
        
        return product
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get(
    "/products-event",
    response_model=List[ProductEventResponseSchema]
)
def list_products_event(
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    limit: int = Query(50, ge=1, le=100, description="Número máximo de produtos (1-100)"),
    offset: int = Query(0, ge=0, description="Número de produtos para pular"),
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    """Lista produtos de eventos"""
    return ProductEventController.list(db, event_id=event_id, limit=limit, offset=offset)


@router.get(
    "/products-event/{product_id}",
    response_model=ProductEventResponseSchema
)
def get_product_event(
    product_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    """Busca um produto por ID"""
    try:
        return ProductEventController.get(db, product_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/events/{event_id}/products-event",
    response_model=List[ProductEventResponseSchema]
)
def get_products_by_event(
    event_id: int,
    limit: int = Query(None, ge=1, le=100, description="Número máximo de produtos (1-100)"),
    offset: int = Query(0, ge=0, description="Número de produtos para pular"),
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    """Busca produtos de um evento com paginação opcional"""
    try:
        return ProductEventController.get_by_event(db, event_id, limit=limit, offset=offset)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/products-event/{product_id}",
    response_model=ProductEventResponseSchema
)
def update_product_event(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    stock: Optional[int] = Form(None),
    last_pieces: Optional[bool] = Form(None),
    event_id: Optional[int] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    replace_images: bool = Form(False),
    removed_image_ids: Optional[str] = Form(None),  # Lista de IDs separados por vírgula
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master)
):
    """Atualiza um produto de evento"""
    data = {}
    
    if name is not None:
        data["name"] = name
    if description is not None:
        data["description"] = description
    if price is not None:
        try:
            price_decimal = Decimal(price)
            if price_decimal < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="O preço não pode ser negativo"
                )
            data["price"] = price_decimal
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Preço inválido"
            )
    if status is not None:
        if status not in ["active", "inactive"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status inválido. Use 'active' ou 'inactive'"
            )
        data["status"] = status
    if stock is not None:
        if stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O estoque não pode ser negativo"
            )
        data["stock"] = stock
    if last_pieces is not None:
        data["last_pieces"] = last_pieces
    if event_id is not None:
        data["event_id"] = event_id
    
    # Processa IDs de imagens removidas
    if removed_image_ids:
        try:
            # Converte string de IDs separados por vírgula para lista de inteiros
            image_ids_list = [int(id_str.strip()) for id_str in removed_image_ids.split(",") if id_str.strip()]
            if image_ids_list:
                data["removed_image_ids"] = image_ids_list
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato inválido para IDs de imagens removidas"
            )
    
    try:
        return ProductEventController.update(
            db, product_id, data, user, 
            image_files=images, 
            replace_images=replace_images
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete(
    "/products-event/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_product_event(
    product_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin_or_master)
):
    """Deleta um produto de evento (soft delete)"""
    try:
        ProductEventController.delete(db, product_id, user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

