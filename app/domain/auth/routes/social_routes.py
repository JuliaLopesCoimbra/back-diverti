from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.config.auth_db import get_db
from app.infra.oauth.google import GoogleOAuth
from app.infra.oauth.facebook import FacebookOAuth
from app.domain.auth.controllers.social_login_controller import SocialLoginController
from app.domain.auth.schemas.auth_schema import TokenResponse
import uuid

router = APIRouter(prefix="/auth", tags=["Social Login"])

@router.get("/google/init")
def google_init():
    state = str(uuid.uuid4())
    url = GoogleOAuth.get_authorization_url(state)
    return {"auth_url": url, "state": state}


@router.get("/google/callback")
def google_callback(request: Request, db: Session = Depends(get_db)):
    # Verifica se há erro retornado pelo provider
    error = request.query_params.get("error")
    if error:
        error_description = request.query_params.get("error_description", "Erro na autenticação")
        from fastapi.responses import RedirectResponse
        from app.config.settings import settings
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/pages/auth/login?error={error}&message={error_description}",
            status_code=302
        )
    
    code = request.query_params.get("code")
    if not code:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Código de autorização não fornecido.")
    
    agent = request.headers.get("user-agent")
    ip = request.client.host

    return SocialLoginController.google_callback(
        db, code, agent, ip
    )


@router.get("/facebook/init")
def facebook_init():
    state = str(uuid.uuid4())
    url = FacebookOAuth.get_authorization_url(state)
    return {"auth_url": url, "state": state}


@router.get("/facebook/callback")
def facebook_callback(request: Request, db: Session = Depends(get_db)):
    from fastapi.responses import RedirectResponse
    from fastapi import HTTPException
    from app.config.settings import settings
    from urllib.parse import quote
    
    # Verifica se há erro retornado pelo provider
    error = request.query_params.get("error")
    if error:
        error_description = request.query_params.get("error_description", "Erro na autenticação")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/pages/auth/login?error={error}&message={quote(error_description)}",
            status_code=302
        )
    
    code = request.query_params.get("code")
    if not code:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/pages/auth/login?error=no_code&message={quote('Código de autorização não fornecido.')}",
            status_code=302
        )
    
    agent = request.headers.get("user-agent")
    ip = request.client.host

    try:
        return SocialLoginController.facebook_callback(
            db, code, agent, ip
        )
    except HTTPException as e:
        # Redireciona para login com mensagem de erro
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/pages/auth/login?error=facebook_error&message={quote(e.detail)}",
            status_code=302
        )
    except Exception as e:
        # Captura outros erros inesperados
        error_msg = str(e) if str(e) else "Erro inesperado ao autenticar com Facebook"
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/pages/auth/login?error=facebook_error&message={quote(error_msg)}",
            status_code=302
        )

@router.get("/instagram/init")
def instagram_init():
    state = str(uuid.uuid4())
    url = InstagramOAuth.get_authorization_url(state)
    return {"auth_url": url, "state": state}


@router.get("/instagram/callback", response_model=TokenResponse)
def instagram_callback(code: str, state: str, request: Request, db: Session = Depends(get_db)):
    agent = request.headers.get("user-agent")
    ip = request.client.host

    access, refresh, user = SocialLoginController.instagram_callback(db, code, agent, ip)

    return TokenResponse(access_token=access, refresh_token=refresh)