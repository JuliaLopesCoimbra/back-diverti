import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import desc

from app.domain.auth.repositories.auth_repository import AuthRepository
from app.domain.auth.repositories.email_repository import EmailVerificationRepository
from app.domain.auth.repositories.email_log_repository import EmailLogRepository
from app.domain.auth.models.email_verification_model import EmailVerificationToken
from app.domain.auth.models.email_log_model import EmailType, EmailStatus
from app.infra.email_sender import EmailSender
from app.infra.email_templates import EmailTemplates
from app.infra.email_validator import EmailValidator
from app.config.settings import settings

class EmailVerificationService:
    @staticmethod
    def resend_verification_email(db, email: str):
        user = AuthRepository.get_user_by_email(db, email)

        # resposta genérica (segurança)
        if not user:
            return {
                "message": "Se o email existir, enviaremos um novo link de verificação."
            }

        if user.is_email_verified:
            return {
                "message": "Este email já foi verificado."
            }

        # Verificar cooldown de 1 minuto
        last_token = EmailVerificationRepository.get_last_token_for_user(db, user.id)
        if last_token and last_token.created_at:
            # Garantir que ambos os timestamps estão em UTC
            now = datetime.now(timezone.utc)
            last_created = last_token.created_at
            # Se created_at não tem timezone, assumir UTC
            if last_created.tzinfo is None:
                last_created = last_created.replace(tzinfo=timezone.utc)
            else:
                last_created = last_created.astimezone(timezone.utc)
            
            time_since_last = now - last_created
            if time_since_last < timedelta(minutes=1):
                seconds_remaining = int((timedelta(minutes=1) - time_since_last).total_seconds())
                raise HTTPException(
                    status_code=429,
                    detail=f"Aguarde {seconds_remaining} segundos antes de solicitar um novo email."
                )

        # envia novo email
        EmailVerificationService.send_verification_email(db, user)

        return {
            "message": "Novo email de verificação enviado. Verifique também sua pasta de spam."
        }

    @staticmethod
    def send_verification_email(db, user):
        import logging
        logger = logging.getLogger(__name__)
        
        token = str(uuid.uuid4())
        expires = datetime.now(timezone.utc) + timedelta(hours=24)

        logger.info(f"Criando token de verificação para usuário {user.id} (email: {user.email})")
        token_model = EmailVerificationRepository.create_token(db, user.id, token, expires)
        logger.info(f"Token criado com sucesso: {token[:20]}... (ID: {token_model.id})")

        link = f"{settings.FRONTEND_URL}/pages/auth/verify-email?token={token}"

        # Validar email antes de enviar
        validation_result = EmailValidator.validate_email_comprehensive(user.email, check_mx=False)
        email_validated = validation_result.get("is_valid", False)
        validation_errors = ", ".join(validation_result.get("errors", []))
        mx_server = validation_result.get("mx_server")

        # Criar log ANTES de enviar
        email_log = EmailLogRepository.create_log(
            db=db,
            recipient_email=user.email,
            subject="Confirme seu e-mail - N1 App",
            email_type=EmailType.VERIFICATION,
            user_id=user.id,
            status=EmailStatus.PENDING,
            extra_data={"token_id": token_model.id}
        )
        
        # Atualizar informações de validação no log
        EmailLogRepository.update_validation_info(
            db=db,
            log_id=email_log.id,
            email_validated=email_validated,
            validation_errors=validation_errors if not email_validated else None,
            mx_server=mx_server
        )

        # Usar template profissional
        html = EmailTemplates.verification_email(user.name, link)

        # Enviar email com log
        send_result = EmailSender.send_email(
            user.email,
            "Confirme seu e-mail - N1 App",
            html,
            db_session=db,
            email_log_id=email_log.id
        )
        
        if send_result["success"]:
            logger.info(f"Email de verificação enviado para {user.email} (Log ID: {email_log.id})")
        else:
            logger.error(f"Falha ao enviar email de verificação para {user.email}: {send_result.get('error_message')} (Log ID: {email_log.id})")
            # Não levantar exceção aqui para não quebrar o fluxo, mas o log já foi criado

        return {"message": "Email de verificação enviado."}

    @staticmethod
    def verify_email(db, token: str):
        import logging
        from app.core.security.jwt import JWTHandler
        from urllib.parse import urlencode
        from app.config.settings import settings
        
        logger = logging.getLogger(__name__)
        
        if not token or not token.strip():
            logger.warning("Tentativa de verificação com token vazio")
            raise HTTPException(status_code=400, detail="Token inválido.")
        
        # Limpar token
        token_clean = token.strip()
        logger.info(f"Buscando token: {token_clean[:20]}... (tamanho: {len(token_clean)})")
        
        token_model = EmailVerificationRepository.get_token(db, token_clean)

        if not token_model:
            # Tentar buscar todos os tokens recentes para debug
            recent_tokens = db.query(EmailVerificationToken).order_by(desc(EmailVerificationToken.created_at)).limit(5).all()
            logger.warning(f"Token não encontrado. Tokens recentes no banco: {[t.token[:20] + '...' for t in recent_tokens]}")
            logger.warning(f"Token não encontrado ou já utilizado: {token_clean[:20]}...")
            raise HTTPException(status_code=400, detail="Token inválido ou já utilizado.")

        # Verificar se já foi usado (dupla verificação)
        if token_model.used_at:
            logger.warning(f"Tentativa de usar token já utilizado: {token[:10]}...")
            raise HTTPException(status_code=400, detail="Token já foi utilizado.")

        # Verificar expiração
        now = datetime.now(timezone.utc)
        if token_model.expires_at.tzinfo is None:
            expires_at = token_model.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = token_model.expires_at.astimezone(timezone.utc)
            
        if now > expires_at:
            logger.warning(f"Tentativa de usar token expirado: {token[:10]}...")
            raise HTTPException(status_code=400, detail="Token expirado.")

        user = token_model.user
        if not user:
            logger.error(f"Token sem usuário associado: {token[:10]}...")
            raise HTTPException(status_code=400, detail="Token inválido.")

        # Marcar como usado ANTES de atualizar o usuário (evitar uso duplo)
        EmailVerificationRepository.mark_used(db, token_model)
        db.flush()  # Garantir que a marcação seja persistida antes de continuar

        # Atualizar usuário
        user.is_email_verified = True
        db.commit()
        db.refresh(user)

        # Verificar se precisa completar outras etapas
        needs_age_verification = not user.age_verified
        needs_profile_completion = not user.cpf or not user.gender

        result = {
            "message": "Email confirmado com sucesso!",
            "needs_age_verification": needs_age_verification,
            "needs_profile_completion": needs_profile_completion
        }

        # Se precisa de outras etapas, criar token temporário
        if needs_age_verification or needs_profile_completion:
            temp_token = JWTHandler.create_access_token({
                "sub": str(user.id),
                "role": user.role,
                "temp": True
            }, expires_minutes=30)
            
            result["temp_token"] = temp_token

        return result

    @staticmethod
    def send_first_access_email(db, user):
        import logging
        logger = logging.getLogger(__name__)
        
        token = str(uuid.uuid4())
        expires = datetime.now(timezone.utc) + timedelta(hours=24)
        token_model = EmailVerificationRepository.create_token(db, user.id, token, expires)

        link = f"{settings.FRONTEND_URL}/pages/auth/first-access?token={token}"

        # Validar email antes de enviar
        validation_result = EmailValidator.validate_email_comprehensive(user.email, check_mx=False)
        email_validated = validation_result.get("is_valid", False)
        validation_errors = ", ".join(validation_result.get("errors", []))
        mx_server = validation_result.get("mx_server")

        # Criar log ANTES de enviar
        email_log = EmailLogRepository.create_log(
            db=db,
            recipient_email=user.email,
            subject="Primeiro acesso ao sistema - N1 App",
            email_type=EmailType.FIRST_ACCESS,
            user_id=user.id,
            status=EmailStatus.PENDING,
            extra_data={"token_id": token_model.id}
        )
        
        # Atualizar informações de validação no log
        EmailLogRepository.update_validation_info(
            db=db,
            log_id=email_log.id,
            email_validated=email_validated,
            validation_errors=validation_errors if not email_validated else None,
            mx_server=mx_server
        )

        # Usar template profissional
        html = EmailTemplates.first_access_email(user.name, link)

        # Enviar email com log
        send_result = EmailSender.send_email(
            user.email,
            "Primeiro acesso ao sistema - N1 App",
            html,
            db_session=db,
            email_log_id=email_log.id
        )
        
        if send_result["success"]:
            logger.info(f"Email de primeiro acesso enviado para {user.email} (Log ID: {email_log.id})")
        else:
            logger.error(f"Falha ao enviar email de primeiro acesso para {user.email}: {send_result.get('error_message')} (Log ID: {email_log.id})")
