import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import logging
from app.domain.auth.repositories.password_reset_repository import PasswordResetRepository
from app.domain.auth.repositories.auth_repository import AuthRepository
from app.domain.auth.repositories.email_log_repository import EmailLogRepository
from app.domain.auth.models.email_log_model import EmailType, EmailStatus
from app.infra.email_sender import EmailSender
from app.infra.email_templates import EmailTemplates
from app.infra.email_validator import EmailValidator
from app.core.security.hashing import Hash
from app.core.security.password_validator import validate_password
from app.config.settings import settings

logger = logging.getLogger(__name__)

class PasswordResetService:

    @staticmethod
    def send_reset_email(db, email: str):
        user = AuthRepository.get_user_by_email(db, email)

        # Verificar se o email existe no banco de dados
        if not user:
            raise HTTPException(
                status_code=404,
                detail="Email não encontrado. Verifique se o email está correto."
            )

        token = str(uuid.uuid4())
        expires = datetime.utcnow() + timedelta(hours=1)

        token_model = PasswordResetRepository.create_token(db, user.id, token, expires)

        link = f"{settings.FRONTEND_URL}/pages/auth/reset-password?token={token}"

        # Validar email antes de enviar
        validation_result = EmailValidator.validate_email_comprehensive(user.email, check_mx=False)
        email_validated = validation_result.get("is_valid", False)
        validation_errors = ", ".join(validation_result.get("errors", []))
        mx_server = validation_result.get("mx_server")

        # Criar log ANTES de enviar
        email_log = EmailLogRepository.create_log(
            db=db,
            recipient_email=user.email,
            subject="Recuperação de Senha - N1 App",
            email_type=EmailType.PASSWORD_RESET,
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
        html = EmailTemplates.password_reset_email(link)

        # Enviar email com log
        send_result = EmailSender.send_email(
            user.email,
            "Recuperação de Senha - N1 App",
            html,
            db_session=db,
            email_log_id=email_log.id
        )
        
        if send_result["success"]:
            logger.info(f"Email de recuperação enviado para {user.email} (Log ID: {email_log.id})")
        else:
            logger.error(f"Falha ao enviar email de recuperação para {user.email}: {send_result.get('error_message')} (Log ID: {email_log.id})")

        return {"message": "Email de recuperação enviado com sucesso! Verifique sua caixa de entrada."}


    @staticmethod
    def reset_password(db, token: str, new_password: str):
        # Validação de senha
        validate_password(new_password)
        
        token_model = PasswordResetRepository.get_token(db, token)

        if not token_model:
            raise HTTPException(status_code=400, detail="Token inválido ou já utilizado.")

        if datetime.now(timezone.utc) > token_model.expires_at:
            raise HTTPException(status_code=400, detail="Token expirado.")

        # Atualizar senha
        user = token_model.user
        user.password_hash = Hash.hash_password(new_password)

        # Marcar o token como usado
        PasswordResetRepository.mark_used(db, token_model)

        db.commit()

        return {"message": "Senha redefinida com sucesso!"}
