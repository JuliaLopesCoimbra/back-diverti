from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from app.config.admin_db import get_admin_db
from app.config.auth_db import get_db
from app.config.interaction_db import get_interaction_db
from app.domain.users.controllers.comment_controller import CommentController
from app.domain.admin.controllers.news_controller import NewsController
from app.domain.auth.controllers.auth_controller import get_current_user  # A dependência criada
from app.core.security.auth_dependency import get_current_user_optional
from app.domain.auth.models.user_model import User
from app.infra.redis import check_rate_limit

router = APIRouter(prefix="/news", tags=["News"])


# 🔹 Listar comentários
@router.get("/{news_id}/comments")
def list_comments(
    news_id: int,
    limit: int = Query(50, ge=1, le=100, description="Número máximo de comentários (1-100)"),
    offset: int = Query(0, ge=0, description="Número de comentários para pular"),
    interaction_db=Depends(get_interaction_db),
    auth_db=Depends(get_db),
    user=Depends(get_current_user_optional)
):
    """Lista comentários de uma notícia com paginação obrigatória"""
    user_id = user.id if user else None
    return CommentController.list(interaction_db, news_id, auth_db, user_id, None, limit, offset)


# 🔹 Criar comentário
@router.post("/{news_id}/comments")
def create_comment(
    news_id: int,
    content: str,
    background_tasks: BackgroundTasks,
    interaction_db=Depends(get_interaction_db),
    auth_db=Depends(get_db),
    admin_db=Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    if not content:
        raise HTTPException(
            status_code=400,
            detail="Conteúdo do comentário não pode estar vazio."
        )
    
    # Rate limiting: 10 comentários por minuto por usuário
    allowed, remaining = check_rate_limit(f"comment:user:{user.id}", max_requests=10, window_seconds=60)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Muitos comentários. Tente novamente em 1 minuto.",
            headers={"Retry-After": "60", "X-RateLimit-Remaining": str(remaining)}
        )

    return CommentController.create(
        interaction_db,
        auth_db,
        admin_db,
        content,
        news_id,
        user.id,
        None,
        background_tasks
    )


# 🔹 Criar resposta a um comentário
@router.post("/{news_id}/comments/{comment_id}/replies")
def create_reply(
    news_id: int,
    comment_id: int,
    content: str,
    background_tasks: BackgroundTasks,
    interaction_db=Depends(get_interaction_db),
    auth_db=Depends(get_db),
    admin_db=Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    if not content:
        raise HTTPException(
            status_code=400,
            detail="Conteúdo da resposta não pode estar vazio."
        )
    
    # Rate limiting: 10 respostas por minuto por usuário
    allowed, remaining = check_rate_limit(f"reply:user:{user.id}", max_requests=10, window_seconds=60)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Muitas respostas. Tente novamente em 1 minuto.",
            headers={"Retry-After": "60", "X-RateLimit-Remaining": str(remaining)}
        )
    
    return CommentController.create(
        interaction_db,
        auth_db,
        admin_db,
        content,
        news_id,
        user.id,
        parent_comment_id=comment_id,
        background_tasks=background_tasks
    )


# 🔹 Listar respostas de um comentário
@router.get("/{news_id}/comments/{comment_id}/replies")
def list_replies(
    news_id: int,
    comment_id: int,
    limit: int = Query(50, ge=1, le=100, description="Número máximo de respostas (1-100)"),
    offset: int = Query(0, ge=0, description="Número de respostas para pular"),
    interaction_db=Depends(get_interaction_db),
    auth_db=Depends(get_db),
    user=Depends(get_current_user_optional)
):
    """Lista respostas de um comentário com paginação obrigatória"""
    user_id = user.id if user else None
    return CommentController.list(
        interaction_db, news_id, auth_db, user_id, parent_comment_id=comment_id, limit=limit, offset=offset
    )


# 🔹 Curtir comentário
@router.post("/comments/{comment_id}/likes")
def like_comment(
    comment_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    interaction_db=Depends(get_interaction_db),
    admin_db=Depends(get_admin_db),
    user: User = Depends(get_current_user)
):
    from app.domain.users.controllers.comment_like_controller import CommentLikeController
    # Extrai IP e User-Agent do request
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return CommentLikeController.create(interaction_db, admin_db, comment_id, user, ip_address, user_agent, background_tasks)


# 🔹 Descurtir comentário
@router.delete("/comments/{comment_id}/likes")
def unlike_comment(
    comment_id: int,
    background_tasks: BackgroundTasks,
    interaction_db=Depends(get_interaction_db),
    user: User = Depends(get_current_user)
):
    from app.domain.users.controllers.comment_like_controller import CommentLikeController
    return CommentLikeController.remove(interaction_db, comment_id, user, background_tasks)


# 🔹 Listar usuários que curtiram um comentário
@router.get("/comments/{comment_id}/likes/users")
def get_users_who_liked_comment(
    comment_id: int,
    limit: int = Query(10, ge=1, le=50, description="Número máximo de usuários (1-50)"),
    offset: int = Query(0, ge=0, description="Número de usuários para pular"),
    interaction_db=Depends(get_interaction_db),
    auth_db=Depends(get_db)
):
    """
    Retorna lista de usuários que curtiram um comentário, com paginação.
    """
    from app.domain.users.controllers.comment_like_controller import CommentLikeController
    return CommentLikeController.get_users_who_liked(
        interaction_db,
        auth_db,
        comment_id,
        limit,
        offset
    )


# 🔹 Excluir comentário (soft delete)
@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    interaction_db=Depends(get_interaction_db),
    user: User = Depends(get_current_user)
):
    from fastapi import status
    
    try:
        return CommentController.delete(
            interaction_db,
            comment_id,
            user.id,
            user.role
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


# 🔹 Buscar news completa com curtidas e comentários
@router.get("/{news_id}/details")
def get_news_details(
    news_id: int,
    event_id: int = Query(None, description="ID do evento (opcional, usado para contexto admin)"),
    admin_db=Depends(get_admin_db),
    interaction_db=Depends(get_interaction_db),
    auth_db=Depends(get_db),
    user=Depends(get_current_user_optional)
):
    """
    Endpoint unificado para buscar uma news completa com todas as informações:
    - Dados da news
    - Quantidade de curtidas
    - Se o usuário curtiu (se autenticado)
    - Lista de comentários com informações dos usuários
    
    Se event_id for fornecido (contexto admin):
    - Permite visualizar posts pendentes/rejeitados
    - Valida se a news pertence ao evento
    
    Se event_id não for fornecido (contexto público):
    - Só retorna posts aprovados
    - EXCETO se o usuário autenticado for o autor do post (pode ver seus próprios posts rejeitados)
    """
    from app.domain.admin.repositories.news_repository import NewsRepository
    from app.domain.admin.models.news_model import NewsPost
    from fastapi import HTTPException
    
    # OTIMIZAÇÃO: Validação mais rápida - busca apenas campos necessários (sem imagens)
    # Busca apenas os campos necessários para validação (mais rápido que carregar tudo)
    news_check = admin_db.query(NewsPost.id, NewsPost.event_id, NewsPost.status, NewsPost.author_id).filter(
        NewsPost.id == news_id,
        NewsPost.status != "deleted",
        NewsPost.deleted_at.is_(None)
    ).first()
    
    if not news_check:
        raise HTTPException(status_code=404, detail="Notícia não encontrada.")
    
    # Se event_id foi fornecido (contexto admin), valida se pertence ao evento
    if event_id is not None:
        if news_check.event_id != event_id:
            raise HTTPException(status_code=404, detail="Notícia não encontrada.")
        # Em contexto admin, permite ver qualquer status
    else:
        # Em contexto público, só permite posts aprovados
        # EXCETO se o usuário for o autor do post (pode ver seus próprios posts rejeitados)
        if news_check.status != "approved":
            # Verifica se o usuário é o autor
            if not user or user.id != news_check.author_id:
                raise HTTPException(status_code=404, detail="Notícia não encontrada.")
    
    user_id = user.id if user else None
    return NewsController.get_with_details(admin_db, interaction_db, auth_db, news_id, user_id)
