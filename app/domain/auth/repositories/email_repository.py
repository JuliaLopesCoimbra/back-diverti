from sqlalchemy.orm import Session
from app.domain.auth.models.email_verification_model import EmailVerificationToken
from datetime import datetime, timezone
from sqlalchemy import desc

class EmailVerificationRepository:

    @staticmethod
    def create_token(db: Session, user_id: int, token: str, expires_at):
        import logging
        logger = logging.getLogger(__name__)
        
        model = EmailVerificationToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(model)
        db.commit()
        db.refresh(model)  # Garantir que o modelo está atualizado
        
        logger.info(f"Token salvo no banco - ID: {model.id}, Token: {token[:20]}..., User ID: {user_id}")
        
        # Verificar se foi salvo corretamente
        verify = db.query(EmailVerificationToken).filter(EmailVerificationToken.id == model.id).first()
        if not verify:
            logger.error(f"ERRO: Token não foi salvo corretamente! ID: {model.id}")
        else:
            logger.info(f"Token verificado no banco - Token salvo: {verify.token[:20]}...")
        
        return model

    @staticmethod
    def get_token(db: Session, token: str):
        import logging
        logger = logging.getLogger(__name__)
        
        # Limpar token (remover espaços)
        token_clean = token.strip() if token else ""
        
        # Buscar token
        token_model = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token_clean,
            EmailVerificationToken.used_at == None
        ).first()
        
        if not token_model:
            # Tentar buscar sem filtro de used_at para debug
            token_any = db.query(EmailVerificationToken).filter(
                EmailVerificationToken.token == token_clean
            ).first()
            if token_any:
                logger.warning(f"Token encontrado mas já foi usado: {token_clean[:10]}... (usado em: {token_any.used_at})")
            else:
                logger.warning(f"Token não encontrado no banco: {token_clean[:10]}...")
        
        return token_model

    @staticmethod
    def mark_used(db: Session, model: EmailVerificationToken):
        model.used_at = datetime.now(timezone.utc)
        db.commit()

    @staticmethod
    def get_last_token_for_user(db: Session, user_id: int):
        """Retorna o último token criado para um usuário (usado ou não)"""
        return db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user_id
        ).order_by(desc(EmailVerificationToken.created_at)).first()

