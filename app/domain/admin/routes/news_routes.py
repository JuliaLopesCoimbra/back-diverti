from fastapi import APIRouter, Depends, HTTPException, Form, Query
from fastapi import UploadFile, File
from typing import List, Optional
from app.config.admin_db import get_admin_db
from app.config.auth_db import get_db
from app.config.interaction_db import get_interaction_db
from app.core.security.auth_dependency import get_current_user, get_current_user_optional
from app.core.security.permissions import require_colunista_or_above, require_subadmin_or_master
from app.domain.admin.controllers.news_controller import NewsController
from app.domain.auth.controllers.auth_controller import AuthController
from app.infra.s3_upload import upload_image_to_s3
router = APIRouter(prefix="/admin/events", tags=["Admin News"])

# ===== ROTAS ESPECÍFICAS (devem vir ANTES das rotas com {event_id}) =====

# Endpoint para listar posts do usuário autenticado
@router.get("/my-posts")
def list_my_posts(
    db = Depends(get_admin_db),
    user = Depends(require_colunista_or_above),
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de posts (1-100)"),
    offset: int = Query(0, ge=0, description="Número de posts para pular")
):
    return NewsController.list_by_author(db, user.id, event_id, limit, offset)

# Endpoint para listar posts pendentes do usuário autenticado
@router.get("/my-posts/pending")
def list_my_pending_posts(
    db = Depends(get_admin_db),
    user = Depends(require_colunista_or_above),
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de posts (1-100)"),
    offset: int = Query(0, ge=0, description="Número de posts para pular")
):
    return NewsController.list_pending_by_author(db, user.id, event_id, limit, offset)

# Endpoint para listar posts rejeitados pelo admin/subadmin autenticado
@router.get("/my-rejected-posts")
def list_my_rejected_posts(
    db = Depends(get_admin_db),
    rejector = Depends(require_subadmin_or_master),
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de posts (1-100)"),
    offset: int = Query(0, ge=0, description="Número de posts para pular")
):
    return NewsController.list_rejected_by_rejector(db, rejector, event_id, limit, offset)

# Endpoint para listar posts pendentes de aprovação
@router.get("/news/pending")
def list_pending_posts(
    db = Depends(get_admin_db),
    approver = Depends(require_subadmin_or_master),
    event_id: Optional[int] = Query(None, description="Filtrar por evento"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de posts (1-100)"),
    offset: int = Query(0, ge=0, description="Número de posts para pular")
):
    return NewsController.list_pending(db, approver, event_id, limit, offset)

# Endpoint para aprovar um post
@router.post("/news/{post_id}/approve")
def approve_post(
    post_id: int,
    db = Depends(get_admin_db),
    approver = Depends(require_subadmin_or_master)
):
    return NewsController.approve(db, post_id, approver)

# Endpoint para rejeitar um post
@router.post("/news/{post_id}/reject")
def reject_post(
    post_id: int,
    db = Depends(get_admin_db),
    rejector = Depends(require_subadmin_or_master)
):
    return NewsController.reject(db, post_id, rejector)

# Endpoint para desativar um post
@router.post("/news/{post_id}/deactivate")
def deactivate_post(
    post_id: int,
    db = Depends(get_admin_db),
    deactivator = Depends(require_subadmin_or_master)
):
    return NewsController.deactivate(db, post_id, deactivator)

@router.post("/upload-image")
def upload_image(image: UploadFile = File(...)):
    try:
        image_url = upload_image_to_s3(image)
        return {"image_url": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ROTAS COM {event_id} (devem vir DEPOIS das rotas específicas) =====

# Endpoint para criar notícia
@router.post("/{event_id}/news")
def create_news(
    event_id: int,
    title: str = Form(...),
    content: str = Form(...),
    images: list[UploadFile] = File(...),
    db = Depends(get_admin_db),
    user = Depends(require_colunista_or_above)
):
    # Validação: máximo de 5 imagens
    if len(images) > 5:
        raise HTTPException(status_code=400, detail="Máximo de 5 imagens permitidas por post.")
    
    if len(images) == 0:
        raise HTTPException(status_code=400, detail="Pelo menos uma imagem é obrigatória.")

    data = {
        "title": title,
        "content": content,
        "author_id": user.id,
        "event_id": event_id
    }

    return NewsController.create(db, data, user, image_files=images)



# Endpoint para listar todas as notícias
@router.get("/{event_id}/news")
def list_news_by_event(
    event_id: int,
    db = Depends(get_admin_db),
    user = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    return NewsController.list_by_event(db, event_id, limit, offset)




# Endpoint para editar uma notícia
@router.put("/{event_id}/news/{news_id}")
def update_news(
    event_id: int,
    news_id: int,
    title: str = Form(...),
    content: str = Form(...),
    images: list[UploadFile] = File(None),
    replace_all: bool = Form(False),
    db = Depends(get_admin_db),
    user = Depends(require_colunista_or_above)
):

    news = NewsController.get(db, news_id)
    if not news or news.event_id != event_id:
        raise HTTPException(status_code=404, detail="Notícia não encontrada.")

    # Verifica se o admin é o autor da news antes de atualizar
    if news.author_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Você só pode editar notícias que você criou."
        )

    # Validação: máximo de 5 imagens
    if images and len(images) > 5:
        raise HTTPException(status_code=400, detail="Máximo de 5 imagens permitidas por post.")

    return NewsController.update(db, news_id, title, content, images, user, replace_all)



# Endpoint para deletar uma notícia
@router.delete("/{event_id}/news/{news_id}")
def delete_news(
    event_id: int,
    news_id: int,
    db = Depends(get_admin_db),
    user = Depends(require_colunista_or_above)
):

    # Verifica se a news existe e pertence ao evento
    news = NewsController.get(db, news_id)
    if not news or news.event_id != event_id:
        raise HTTPException(status_code=404, detail="Notícia não encontrada.")

    # Verifica se o admin é o autor da news antes de deletar
    if news.author_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Você só pode deletar notícias que você criou."
        )

    NewsController.delete(db, news_id, user)
    return {"message": "Notícia removida com sucesso."}

# Endpoint para ver uma notícia específica (público)
@router.get("/{event_id}/news/{news_id}")
def get_news_by_id(
    event_id: int,
    news_id: int,
    db = Depends(get_admin_db),
    user = Depends(get_current_user)
):
    news = NewsController.get(db, news_id)

    if not news or news.event_id != event_id:
        raise HTTPException(status_code=404, detail="Notícia não encontrada.")

    return news

# Endpoint removido - unificado em /news/{news_id}/details
# Use o endpoint unificado em comment_routes.py com event_id como query parameter

