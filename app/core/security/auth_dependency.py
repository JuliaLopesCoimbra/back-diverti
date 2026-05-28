from fastapi import Depends, Request,HTTPException, status
from app.core.security.jwt import JWTHandler
from app.core.exceptions.auth_exceptions import Unauthorized
from sqlalchemy.orm import Session
from app.config.auth_db import get_db
from app.domain.auth.models.user_model import User
from app.infra.redis import redis_client, CacheKeys
from typing import Optional

def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise Unauthorized("Token não fornecido.")


    if not auth_header.startswith("Bearer "):
        raise Unauthorized("Formato de token inválido.")

    token = auth_header.split(" ")[1]

    try:
        payload = JWTHandler.decode_token(token)  # Decodifica o token JWT
    except Exception:
        raise Unauthorized("Token inválido ou expirado.")

    user_id = payload.get("sub")  # Obtém o user_id do token
    if not user_id:
        raise Unauthorized("Token sem usuário válido.")

    user_id_int = int(user_id)
    
    # Tenta buscar do cache Redis primeiro
    cached_user = _get_user_from_cache(user_id_int)
    
    if cached_user:
        # Valida status do cache
        if cached_user.get("status") != "active":
            raise Unauthorized("Usuário desativado ou banido.")
        # Retorna objeto User criado a partir do cache
        return _create_user_from_cache(cached_user)
    
    # Se não está no cache, busca do banco
    user = db.query(User).filter(User.id == user_id_int).first()

    if not user:
        raise Unauthorized("Usuário não encontrado.")

    if user.status != "active":
        raise Unauthorized("Usuário desativado ou banido.")

    # Salva no cache para próximas requisições
    _cache_user(user)

    return user  # Retorna o objeto User

def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
):
    auth_header = request.headers.get("Authorization")

    #SEM TOKEN → apenas retorna None
    if not auth_header:
        return None

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]

    try:
        payload = JWTHandler.decode_token(token)
    except Exception:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user_id_int = int(user_id)
    
    # Tenta buscar do cache
    cached_user = _get_user_from_cache(user_id_int)
    
    if cached_user:
        if cached_user.get("status") != "active":
            return None
        return _create_user_from_cache(cached_user)
    
    # Busca do banco
    user = db.query(User).filter(User.id == user_id_int).first()

    if not user:
        return None

    if user.status != "active":
        return None

    # Salva no cache
    _cache_user(user)

    return user

def require_admin(user: User = Depends(get_current_user)):
    """Mantido para compatibilidade - aceita admin_master ou subadmin"""
    if user.role not in ["admin", "admin_master", "subadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem acessar este recurso."
        )
    return user


# ===== FUNÇÕES AUXILIARES PARA CACHE =====

def _get_user_from_cache(user_id: int) -> Optional[dict]:
    """Busca informações do usuário no cache Redis"""
    cache_key = CacheKeys.user_me(user_id)
    return redis_client.get(cache_key)

def _cache_user(user: User, ttl: int = 900) -> bool:
    """
    Salva informações do usuário no cache Redis
    
    Args:
        user: Objeto User do SQLAlchemy
        ttl: Time to live em segundos (padrão: 15 minutos, mesmo do access token)
    """
    cache_key = CacheKeys.user_me(user.id)
    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "is_email_verified": user.is_email_verified,
        "profile_photo": user.profile_photo,
    }
    return redis_client.set(cache_key, user_data, ttl=ttl)

def _create_user_from_cache(cached_data: dict) -> User:
    """
    Cria um objeto User a partir dos dados do cache
    Isso permite manter compatibilidade com o código existente
    """
    user = User()
    user.id = cached_data["id"]
    user.name = cached_data["name"]
    user.email = cached_data["email"]
    user.role = cached_data["role"]
    user.status = cached_data["status"]
    user.is_email_verified = cached_data.get("is_email_verified", False)
    user.profile_photo = cached_data.get("profile_photo")
    return user

def invalidate_user_cache(user_id: int):
    """
    Invalida o cache de um usuário específico
    Use esta função quando o status ou role do usuário for alterado
    """
    cache_key = CacheKeys.user_me(user_id)
    redis_client.delete(cache_key)