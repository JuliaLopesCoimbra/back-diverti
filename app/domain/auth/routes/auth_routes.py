from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.orm import Session
from app.config.auth_db import get_db
from app.core.security.auth_dependency import get_current_user_optional, require_admin
from app.core.security.permissions import require_admin_master, require_admin_or_master
from app.domain.auth.schemas.auth_schema import RegisterRequest, LoginRequest, TokenResponse, AdminCreateAdminRequest, \
    InviteAdminRequest, FirstAccessRequest, ResendAdminInviteRequest, InvitePatrocinadorRequest, UserResponse, AgeVerificationRequest, CompleteProfileRequest, CompleteEmailRequest, CompleteEmailResponse, UpdateEmailByCpfRequest, UpdateEmailByCpfResponse
from app.domain.auth.controllers.auth_controller import AuthController
from app.domain.auth.schemas.auth_schema import RefreshRequest
from app.domain.auth.services.auth_service import AuthService
from app.infra.redis import redis_client, CacheKeys, check_rate_limit

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(
    body: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # Rate limiting: 5 registros por hora por IP (CRÍTICO - retorna 503 se Redis cair)
    ip = request.client.host
    allowed, remaining = check_rate_limit(f"register:ip:{ip}", max_requests=5, window_seconds=3600, critical=True)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas de registro. Tente novamente em 1 hora.",
            headers={"Retry-After": "3600"}
        )

    agent = request.headers.get("user-agent")
    return AuthController.register(db, body, agent, ip)

@router.post("/invite-admin")
def invite_admin(
    body: InviteAdminRequest,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    return AuthController.invite_admin(db, body, admin)

@router.post("/first-access")
def first_access(body: FirstAccessRequest, db: Session = Depends(get_db)):
    return AuthController.first_access(db, body)

@router.post("/resend-admin-invite")
def resend_admin_invite(
    body: ResendAdminInviteRequest,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    return AuthController.resend_admin_invite(db, body.email, admin)

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # Rate limiting: 5 tentativas de login por minuto por IP (CRÍTICO - retorna 503 se Redis cair)
    ip = request.client.host
    allowed, remaining = check_rate_limit(f"login:ip:{ip}", max_requests=5, window_seconds=60, critical=True)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas de login. Tente novamente em 1 minuto.",
            headers={"Retry-After": "60", "X-RateLimit-Remaining": str(remaining)}
        )

    agent = request.headers.get("user-agent")
    access, refresh = AuthController.login(db, body, agent, ip)

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    # Rate limiting: 20 refresh tokens por minuto por IP
    ip = request.client.host
    allowed, remaining = check_rate_limit(f"refresh:ip:{ip}", max_requests=20, window_seconds=60)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas de refresh. Tente novamente em 1 minuto.",
            headers={"Retry-After": "60"}
        )

    agent = request.headers.get("user-agent")
    access, refresh = AuthController.refresh(db, body.refresh_token, agent, ip)

    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/logout")
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    return AuthController.logout(db, body.refresh_token)

@router.post("/verify-age")
def verify_age(
    body: AgeVerificationRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    agent = request.headers.get("user-agent")
    ip = request.client.host

    return AuthController.verify_age(db, current_user.id, body, agent, ip)

@router.post("/complete-profile", response_model=TokenResponse)
def complete_profile(
    body: CompleteProfileRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    agent = request.headers.get("user-agent")
    ip = request.client.host

    result = AuthController.complete_profile(db, current_user.id, body, agent, ip)

    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"]
    )

@router.post("/complete-email", response_model=CompleteEmailResponse)
def complete_email(
    body: CompleteEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    agent = request.headers.get("user-agent")
    ip = request.client.host

    result = AuthController.complete_email(db, current_user.id, body, agent, ip)

    return CompleteEmailResponse(**result)

@router.post("/update-email-by-cpf", response_model=UpdateEmailByCpfResponse)
def update_email_by_cpf(
    body: UpdateEmailByCpfRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Atualiza o email de um usuário que tem CPF cadastrado mas email não verificado.
    Usado quando o usuário digitou email errado no cadastro.
    """
    # Rate limiting: 5 tentativas por hora por IP (CRÍTICO - retorna 503 se Redis cair)
    ip = request.client.host
    allowed, remaining = check_rate_limit(f"update_email_cpf:ip:{ip}", max_requests=5, window_seconds=3600, critical=True)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas. Tente novamente em 1 hora.",
            headers={"Retry-After": "3600"}
        )

    agent = request.headers.get("user-agent")
    return AuthController.update_email_by_cpf(db, body, agent, ip)

@router.get("/me")
def me(user = Depends(AuthController.require_user)):
    """Retorna dados básicos do usuário autenticado com cache"""
    cache_key = CacheKeys.user_me(user.id)
    cached = redis_client.get(cache_key)
    if cached is not None:
        return cached

    result = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "verified": user.is_email_verified,
        "status": user.status,
        "role": user.role,
    }
    # Cacheia por 5 minutos (300 segundos)
    redis_client.set(cache_key, result, ttl=300)
    return result

@router.post("/invite-admin-user")
def invite_admin_user(
    body: InviteAdminRequest,
    db: Session = Depends(get_db),
    admin_master = Depends(require_admin_master)
):
    return AuthController.invite_admin_user(db, body, admin_master)

@router.post("/invite-patrocinador")
def invite_patrocinador(
    body: InvitePatrocinadorRequest,
    db: Session = Depends(get_db),
    inviter = Depends(require_admin_or_master)
):
    return AuthController.invite_patrocinador(db, body, inviter)

@router.post("/revoke-patrocinador/{patrocinador_id}")
def revoke_patrocinador(
    patrocinador_id: int,
    db: Session = Depends(get_db),
    revoker = Depends(require_admin_or_master)
):
    return AuthController.revoke_patrocinador_access(db, patrocinador_id, revoker)

@router.post("/revoke-admin/{admin_id}")
def revoke_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    admin_master = Depends(require_admin_master)
):
    return AuthController.revoke_admin_access(db, admin_id, admin_master)

@router.post("/revoke-user/{user_id}")
def revoke_user(
    user_id: int,
    db: Session = Depends(get_db),
    revoker = Depends(require_admin_or_master)
):
    return AuthController.revoke_user_access(db, user_id, revoker)

@router.post("/reactivate-patrocinador/{patrocinador_id}")
def reactivate_patrocinador(
    patrocinador_id: int,
    db: Session = Depends(get_db),
    reactivator = Depends(require_admin_or_master)
):
    return AuthController.reactivate_patrocinador_access(db, patrocinador_id, reactivator)

@router.post("/reactivate-admin/{admin_id}")
def reactivate_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    admin_master = Depends(require_admin_master)
):
    return AuthController.reactivate_admin_access(db, admin_id, admin_master)

@router.post("/reactivate-user/{user_id}")
def reactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    reactivator = Depends(require_admin_or_master)
):
    return AuthController.reactivate_user_access(db, user_id, reactivator)

@router.get("/admins", response_model=list[UserResponse])
def list_admins(
    limit: int = Query(50, ge=1, le=100, description="Número máximo de admins (1-100)"),
    offset: int = Query(0, ge=0, description="Número de admins para pular"),
    db: Session = Depends(get_db),
    requester = Depends(require_admin_master)
):
    return AuthController.list_admins(db, requester, limit, offset)

@router.get("/patrocinadores", response_model=list[UserResponse])
def list_patrocinadores(
    limit: int = Query(50, ge=1, le=100, description="Número máximo de patrocinadores (1-100)"),
    offset: int = Query(0, ge=0, description="Número de patrocinadores para pular"),
    db: Session = Depends(get_db),
    requester = Depends(require_admin_or_master)
):
    return AuthController.list_patrocinadores(db, requester, limit, offset)

@router.get("/users", response_model=list[UserResponse])
def list_users(
    limit: int = Query(50, ge=1, le=100, description="Número máximo de usuários (1-100)"),
    offset: int = Query(0, ge=0, description="Número de usuários para pular"),
    db: Session = Depends(get_db),
    requester = Depends(require_admin_or_master)
):
    return AuthController.list_users(db, requester, limit, offset)

@router.post("/admin/cleanup-tokens")
def cleanup_expired_tokens(
    batch_size: int = Query(5000, ge=100, le=10000, description="Número máximo de tokens a deletar (100-10000)"),
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
    """
    Endpoint administrativo para limpeza completa de tokens expirados.
    Remove tokens expirados ou revogados há mais de 7 dias.
    Requer permissão de admin.
    """
    return AuthController.cleanup_expired_tokens(db, batch_size)
