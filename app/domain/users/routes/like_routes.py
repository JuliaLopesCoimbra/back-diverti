from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request

from app.config.interaction_db import get_interaction_db
from app.domain.users.controllers.like_controller import LikeController
from app.domain.auth.controllers.auth_controller import AuthController
from app.config.admin_db import get_admin_db
from app.config.auth_db import get_db
from app.domain.users.repositories.like_repository import LikeRepository
from app.infra.redis import check_rate_limit

router = APIRouter(prefix="/news", tags=["Admin News"])

@router.post("/{news_id}/likes")
def like_news(
    news_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    interaction_db=Depends(get_interaction_db),
    admin_db=Depends(get_admin_db),
    user=Depends(AuthController.require_user)
):
    # Rate limiting: 30 likes por minuto por usuário
    allowed, remaining = check_rate_limit(f"like:user:{user.id}", max_requests=30, window_seconds=60)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Muitas curtidas. Tente novamente em 1 minuto.",
            headers={"Retry-After": "60", "X-RateLimit-Remaining": str(remaining)}
        )
    
    # Extrai IP e User-Agent do request
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return LikeController.create(interaction_db, admin_db, news_id, user, ip_address, user_agent, background_tasks)


@router.delete("/{news_id}/likes")
def remove_like(
    news_id: int,
    background_tasks: BackgroundTasks,
    interaction_db=Depends(get_interaction_db),
    user=Depends(AuthController.require_user)
):
    return LikeController.remove(interaction_db, news_id, user, background_tasks)


@router.get("/{news_id}/likes/count")
def get_likes_count(
    news_id: int,
    interaction_db=Depends(get_interaction_db)
):
    return LikeController.count(interaction_db, news_id)

@router.get("/{news_id}/likes/me")
def did_i_like(
    news_id: int,
    interaction_db=Depends(get_interaction_db),
    user=Depends(AuthController.require_user)
):
    like = LikeRepository.get_like(
        interaction_db,
        news_id,
        user.id
    )
    return {
        "liked": bool(like)
    }

@router.get("/likes/me")
def get_my_liked_posts(
    event_id: int = None,
    limit: int = 10,
    offset: int = 0,
    admin_db=Depends(get_admin_db),
    interaction_db=Depends(get_interaction_db),
    auth_db=Depends(get_db),
    user=Depends(AuthController.require_user)
):
    """
    Retorna todos os posts que o usuário curtiu, opcionalmente filtrado por evento
    """
    return LikeController.get_liked_posts(
        admin_db,
        interaction_db,
        auth_db,
        user,
        event_id,
        limit,
        offset
    )

@router.get("/{news_id}/likes/users")
def get_users_who_liked(
    news_id: int,
    limit: int = Query(10, ge=1, le=50, description="Número máximo de usuários (1-50)"),
    offset: int = Query(0, ge=0, description="Número de usuários para pular"),
    interaction_db=Depends(get_interaction_db),
    auth_db=Depends(get_db)
):
    """
    Retorna lista de usuários que curtiram uma notícia, com paginação.
    """
    return LikeController.get_users_who_liked(
        interaction_db,
        auth_db,
        news_id,
        limit,
        offset
    )
