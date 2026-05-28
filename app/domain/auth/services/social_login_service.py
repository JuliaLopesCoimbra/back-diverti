from datetime import datetime, timedelta
from fastapi import HTTPException
from app.infra.oauth.google import GoogleOAuth
from app.infra.oauth.facebook import FacebookOAuth
from app.domain.auth.repositories.social_repository import SocialRepository
from app.domain.auth.repositories.auth_repository import AuthRepository
from app.core.security.jwt import JWTHandler
from app.domain.auth.models.user_model import User
from urllib.parse import urlencode
from fastapi.responses import RedirectResponse
from app.config.settings import settings

class SocialLoginService:

    @staticmethod
    def _get_user_by_social(db, social):
        # social NÃO tem .user (não existe relationship). Então buscamos manualmente.
        user = db.query(User).filter(User.id == social.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário vinculado ao social login não encontrado.")
        return user

    @staticmethod
    def google_callback(db, code, user_agent, ip):
        tokens = GoogleOAuth.exchange_code(code)

        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Falha ao obter token da Google.")

        info = GoogleOAuth.get_user_info(access_token)

        provider_user_id = info.get("sub")
        email = info.get("email")
        name = info.get("name")

        if not provider_user_id:
            raise HTTPException(status_code=400, detail="ID do Google ausente.")
        if not email:
            raise HTTPException(status_code=400, detail="Email não retornado pela Google.")


        social = SocialRepository.get_by_provider(db, "google", provider_user_id)

        if social:
            user = SocialLoginService._get_user_by_social(db, social)
        else:
            user = AuthRepository.get_user_by_email(db, email)

            if not user:
                user = AuthRepository.create_user(
                    db=db,
                    name=name or "Usuário Google",
                    email=email,
                    password_hash=None,
                    role="user",
                    birth_date=None,
                    age_verified=False
                )
                user.is_email_verified = True
                db.commit()

            SocialRepository.create(
                db=db,
                user_id=user.id,
                provider="google",
                provider_user_id=provider_user_id,
                access_token=access_token,
                refresh_token=tokens.get("refresh_token"),
                expires_at=datetime.utcnow() + timedelta(
                    seconds=tokens.get("expires_in", 3600)
                )
            )

        # Garante que o usuário está atualizado do banco antes de criar o token
        db.refresh(user)
        
        # Verificar se precisa confirmar idade
        if not user.age_verified:
            temp_token = JWTHandler.create_access_token({
                "sub": str(user.id),
                "role": user.role,
                "temp": True
            }, expires_minutes=10)
            
            params = urlencode({
                "temp_token": temp_token,
                "requires_age_verification": "true"
            })
            
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/pages/auth/age-verification?{params}",
                status_code=302
            )
        
        # Verificar se precisa completar perfil (CPF e sexo)
        if not user.cpf or not user.gender:
            temp_token = JWTHandler.create_access_token({
                "sub": str(user.id),
                "role": user.role,
                "temp": True,
                "requires_profile_completion": True
            }, expires_minutes=30)
            
            params = urlencode({
                "temp_token": temp_token,
                "requires_profile_completion": "true"
            })
            
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/pages/auth/complete-profile?{params}",
                status_code=302
            )

        access = JWTHandler.create_access_token({
            "sub": str(user.id),
            "role": user.role
        })
        refresh = JWTHandler.create_refresh_token({"sub": str(user.id)})

        expires = datetime.utcnow() + timedelta(days=30)
        AuthRepository.save_refresh_token(db, user.id, refresh, user_agent, ip, expires)

        # Atualizar last_login
        user.last_login = datetime.utcnow()
        db.commit()

        params = urlencode({
            "access_token": access,
            "refresh_token": refresh
        })

        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/pages/auth/callback?{params}",
            status_code=302
        )

    @staticmethod
    def facebook_callback(db, code, user_agent, ip):
        import logging
        logger = logging.getLogger(__name__)
        
        tokens = FacebookOAuth.exchange_code(code)
        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Falha ao obter token do Facebook.")

        info = FacebookOAuth.get_user_info(access_token)
        
        # Log para debug - ver o que o Facebook está retornando
        logger.info(f"Facebook user info received: {info}")

        provider_user_id = info.get("id")
        email = info.get("email")
        name = info.get("name")

        if not provider_user_id:
            raise HTTPException(status_code=400, detail="Facebook não retornou ID do usuário.")
        
        # Verificar se já existe um usuário com esse provider_user_id
        social = SocialRepository.get_by_provider(db, "facebook", provider_user_id)
        
        # Se o email não foi retornado, redirecionar para coleta de email
        if not email:
            logger.warning(f"Facebook não retornou email para usuário {provider_user_id}. Redirecionando para coleta de email.")
            
            if social:
                # Se já existe usuário, usar ele e redirecionar para coletar email
                user = SocialLoginService._get_user_by_social(db, social)
                # Se o usuário já tem email real (não temporário), continuar normalmente
                if user.email and "@facebook.user" not in user.email and "@facebook.temp" not in user.email:
                    email = user.email
                else:
                    # Redirecionar para coletar email
                    temp_token = JWTHandler.create_access_token({
                        "sub": str(user.id),
                        "role": user.role,
                        "temp": True,
                        "requires_email": True,
                        "provider": "facebook",
                        "provider_user_id": provider_user_id
                    }, expires_minutes=30)
                    
                    params = urlencode({
                        "temp_token": temp_token,
                        "requires_email": "true",
                        "name": name or "Usuário"
                    })
                    
                    return RedirectResponse(
                        url=f"{settings.FRONTEND_URL}/pages/auth/complete-email?{params}",
                        status_code=302
                    )
            else:
                # Criar usuário temporário e redirecionar para coletar email
                temp_email = f"{provider_user_id}@facebook.temp"
                user = AuthRepository.create_user(
                    db=db,
                    name=name or "Usuário Facebook",
                    email=temp_email,
                    password_hash=None,
                    role="user",
                    birth_date=None,
                    age_verified=False
                )
                
                SocialRepository.create(
                    db=db,
                    user_id=user.id,
                    provider="facebook",
                    provider_user_id=provider_user_id,
                    access_token=access_token,
                    refresh_token=None,
                    expires_at=None
                )
                db.commit()
                
                temp_token = JWTHandler.create_access_token({
                    "sub": str(user.id),
                    "role": user.role,
                    "temp": True,
                    "requires_email": True,
                    "provider": "facebook",
                    "provider_user_id": provider_user_id
                }, expires_minutes=30)
                
                params = urlencode({
                    "temp_token": temp_token,
                    "requires_email": "true",
                    "name": name or "Usuário"
                })
                
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/pages/auth/complete-email?{params}",
                    status_code=302
                )

        # Se chegou aqui, temos email do Facebook
        if social:
            user = SocialLoginService._get_user_by_social(db, social)
            # Atualizar email se mudou (de temporário para real)
            if user.email != email and ("@facebook.user" in user.email or "@facebook.temp" in user.email):
                user.email = email
                user.is_email_verified = True
                db.commit()
        else:
            user = AuthRepository.get_user_by_email(db, email)

            if not user:
                user = AuthRepository.create_user(
                    db=db,
                    name=name or "Usuário Facebook",
                    email=email,
                    password_hash=None,
                    role="user",
                    birth_date=None,
                    age_verified=False
                )

            SocialRepository.create(
                db=db,
                user_id=user.id,
                provider="facebook",
                provider_user_id=provider_user_id,
                access_token=access_token,
                refresh_token=None,
                expires_at=None
            )
            user.is_email_verified = True
            db.commit()

        # Garante que o usuário está atualizado do banco antes de criar o token
        db.refresh(user)
        
        # PRIMEIRO: Verificar se o email está verificado (sempre verificar email antes de outras etapas)
        if not user.is_email_verified:
            # Se o email não está verificado, redirecionar para aguardar verificação
            # Mas primeiro, verificar se já tem email real (não temporário)
            if user.email and ("@facebook.user" in user.email or "@facebook.temp" in user.email or "@instagram.user" in user.email):
                # Se tem email temporário, precisa informar email primeiro
                temp_token = JWTHandler.create_access_token({
                    "sub": str(user.id),
                    "role": user.role,
                    "temp": True,
                    "requires_email": True,
                    "provider": "facebook",
                    "provider_user_id": provider_user_id
                }, expires_minutes=30)
                
                params = urlencode({
                    "temp_token": temp_token,
                    "requires_email": "true",
                    "name": name or "Usuário"
                })
                
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/pages/auth/complete-email?{params}",
                    status_code=302
                )
            else:
                # Se tem email real mas não está verificado, redirecionar para aguardar verificação
                temp_token = JWTHandler.create_access_token({
                    "sub": str(user.id),
                    "role": user.role,
                    "temp": True,
                    "requires_email_verification": True
                }, expires_minutes=60)
                
                params = urlencode({
                    "temp_token": temp_token,
                    "email": user.email,
                    "requires_email_verification": "true"
                })
                
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/pages/auth/awaiting-email-verification?{params}",
                    status_code=302
                )
        
        # SEGUNDO: Verificar se precisa confirmar idade (só depois de email verificado)
        if not user.age_verified:
            temp_token = JWTHandler.create_access_token({
                "sub": str(user.id),
                "role": user.role,
                "temp": True
            }, expires_minutes=10)
            
            params = urlencode({
                "temp_token": temp_token,
                "requires_age_verification": "true"
            })
            
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/pages/auth/age-verification?{params}",
                status_code=302
            )
        
        # Verificar se precisa completar perfil (CPF e sexo)
        if not user.cpf or not user.gender:
            temp_token = JWTHandler.create_access_token({
                "sub": str(user.id),
                "role": user.role,
                "temp": True,
                "requires_profile_completion": True
            }, expires_minutes=30)
            
            params = urlencode({
                "temp_token": temp_token,
                "requires_profile_completion": "true"
            })
            
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/pages/auth/complete-profile?{params}",
                status_code=302
            )

        access = JWTHandler.create_access_token({
            "sub": str(user.id),
            "role": user.role
        })
        refresh = JWTHandler.create_refresh_token({"sub": str(user.id)})

        expires = datetime.utcnow() + timedelta(days=30)
        AuthRepository.save_refresh_token(db, user.id, refresh, user_agent, ip, expires)

        # Atualizar last_login
        user.last_login = datetime.utcnow()
        db.commit()

        params = urlencode({
            "access_token": access,
            "refresh_token": refresh
        })

        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/pages/auth/callback?{params}",
            status_code=302
        )

    @staticmethod
    def instagram_callback(db, code, user_agent, ip):
        tokens = InstagramOAuth.exchange_code(code)
        access_token = tokens.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Falha ao obter token do Instagram.")

        info = InstagramOAuth.get_user_info(access_token)

        provider_user_id = info.get("id")
        username = info.get("username")

        if not provider_user_id:
            raise HTTPException(status_code=400, detail="Instagram não retornou ID do usuário.")

        social = SocialRepository.get_by_provider(db, "instagram", provider_user_id)

        if social:
            user = SocialLoginService._get_user_by_social(db, social)
        else:
            fake_email = f"{provider_user_id}@instagram.user"
            user = AuthRepository.get_user_by_email(db, fake_email)

            if not user:
                user = AuthRepository.create_user(
                    db=db,
                    name=username or "Instagram User",
                    email=fake_email,
                    password_hash=None,
                    role="user",
                    birth_date=None,
                    age_verified=False
                )


            SocialRepository.create(
                db=db,
                user_id=user.id,
                provider="instagram",
                provider_user_id=provider_user_id,
                access_token=access_token,
                refresh_token=None,
                expires_at=None
            )

        db.refresh(user)
        
        # Verificar se precisa confirmar idade
        if not user.age_verified:
            temp_token = JWTHandler.create_access_token({
                "sub": str(user.id),
                "role": user.role,
                "temp": True
            }, expires_minutes=10)
            
            params = urlencode({
                "temp_token": temp_token,
                "requires_age_verification": "true"
            })
            
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/pages/auth/age-verification?{params}",
                status_code=302
            )

        access = JWTHandler.create_access_token({
            "sub": str(user.id),
            "role": user.role
        })
        refresh = JWTHandler.create_refresh_token({"sub": str(user.id)})

        expires = datetime.utcnow() + timedelta(days=30)
        AuthRepository.save_refresh_token(db, user.id, refresh, user_agent, ip, expires)

        # Atualizar last_login
        user.last_login = datetime.utcnow()
        db.commit()

        return access, refresh, user
