from sqlalchemy.orm import Session, joinedload
from app.domain.auth.models.user_model import User
from app.domain.auth.models.refresh_token_model import RefreshToken
from datetime import datetime, timedelta, timezone, date
from typing import Optional
from sqlalchemy import and_, or_

class AuthRepository:

    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(
        db: Session, 
        name: str, 
        email: str, 
        password_hash: Optional[str], 
        role: str, 
        invited_by_id: int = None,
        birth_date: Optional[date] = None,
        age_verified: bool = False,
        cpf: Optional[str] = None,
        gender: Optional[str] = None,
        lgpd_accepted: bool = False,
        age_terms_accepted: bool = False,
        marketing_email_accepted: bool = False,
        lgpd_accepted_at: Optional[datetime] = None,
        lgpd_accepted_ip: Optional[str] = None,
        lgpd_accepted_user_agent: Optional[str] = None,
        age_terms_accepted_at: Optional[datetime] = None,
        age_terms_accepted_ip: Optional[str] = None,
        age_terms_accepted_user_agent: Optional[str] = None
    ):
        user = User(
            name=name, 
            email=email, 
            password_hash=password_hash, 
            role=role, 
            invited_by_id=invited_by_id,
            birth_date=birth_date,
            age_verified=age_verified,
            cpf=cpf,
            gender=gender,
            lgpd_accepted=lgpd_accepted,
            age_terms_accepted=age_terms_accepted,
            marketing_email_accepted=marketing_email_accepted,
            lgpd_accepted_at=lgpd_accepted_at,
            lgpd_accepted_ip=lgpd_accepted_ip,
            lgpd_accepted_user_agent=lgpd_accepted_user_agent,
            age_terms_accepted_at=age_terms_accepted_at,
            age_terms_accepted_ip=age_terms_accepted_ip,
            age_terms_accepted_user_agent=age_terms_accepted_user_agent
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def save_refresh_token(db: Session, user_id: int, token: str, agent: str, ip: str, expires_at):
        rt = RefreshToken(
            user_id=user_id,
            refresh_token=token,
            user_agent=agent,
            ip_address=ip,
            expires_at=expires_at
        )
        db.add(rt)
        db.commit()
        return rt

    @staticmethod
    def get_refresh_token(db: Session, token: str):
        """Busca refresh token válido (não revogado e não expirado)"""
        now = datetime.now(timezone.utc)  # Timezone aware
        return db.query(RefreshToken).filter(
            RefreshToken.refresh_token == token,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > now  # Filtra tokens expirados
        ).first()

    @staticmethod
    def revoke_token(db: Session, token_model: RefreshToken):
        token_model.revoked = True
        db.commit()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def revoke_all_user_tokens(db: Session, user_id: int):
        """Revoga todos os refresh tokens ativos de um usuário"""
        tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False
        ).all()
        
        for token in tokens:
            token.revoked = True
        
        db.commit()
        return len(tokens)  # Retorna quantidade de tokens revogados

    @staticmethod
    def list_admins(db: Session, limit: int = 50, offset: int = 0):
        """Lista admins com paginação obrigatória"""
        limit = min(limit, 100)  # Máximo de 100 por requisição
        return db.query(User).options(
            joinedload(User.invited_by),
            joinedload(User.deactivated_by),
            joinedload(User.reactivated_by)
        ).filter(User.role == "admin").order_by(User.created_at.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def list_patrocinadores(db: Session, invited_by_id: int = None, limit: int = 50, offset: int = 0):
        """Lista patrocinadores com paginação obrigatória. Se invited_by_id fornecido, filtra apenas os convidados por esse usuário"""
        limit = min(limit, 100)  # Máximo de 100 por requisição
        query = db.query(User).options(
            joinedload(User.invited_by),
            joinedload(User.deactivated_by),
            joinedload(User.reactivated_by)
        ).filter(User.role == "patrocinador")
        if invited_by_id:
            query = query.filter(User.invited_by_id == invited_by_id)
        return query.order_by(User.created_at.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def list_users(db: Session, limit: int = 50, offset: int = 0):
        """Lista users comuns com paginação obrigatória"""
        limit = min(limit, 100)  # Máximo de 100 por requisição
        return db.query(User).options(
            joinedload(User.invited_by),
            joinedload(User.deactivated_by),
            joinedload(User.reactivated_by)
        ).filter(User.role == "user").order_by(User.created_at.desc()).limit(limit).offset(offset).all()

    @staticmethod
    def cleanup_expired_tokens_lazy(db: Session):
        """
        Limpeza leve e rápida: remove apenas tokens expirados (não revogados).
        Usado durante operações normais para manutenção contínua.
        Retorna o número de tokens deletados.
        """
        now = datetime.now(timezone.utc)  # Timezone aware
        
        # Buscar IDs dos tokens expirados (máximo 100)
        expired_token_ids = db.query(RefreshToken.id).filter(
            RefreshToken.expires_at < now,
            RefreshToken.revoked == False
        ).limit(100).all()
        
        if not expired_token_ids:
            return 0
        
        # Extrair apenas os IDs
        ids = [token_id[0] for token_id in expired_token_ids]
        
        # Deletar por IDs (mais confiável que delete direto com limit)
        deleted_count = db.query(RefreshToken).filter(
            RefreshToken.id.in_(ids)
        ).delete(synchronize_session=False)
        
        db.commit()
        return deleted_count

    @staticmethod
    def delete_expired_tokens(db: Session, batch_size: int = 1000):
        """
        Remove tokens expirados ou revogados há mais de 7 dias.
        Retorna o número de tokens deletados.
        
        Args:
            batch_size: Número máximo de tokens a deletar por vez (evita locks longos)
        """
        now = datetime.now(timezone.utc)  # Timezone aware
        
        # Tokens expirados há mais de 7 dias OU revogados há mais de 7 dias
        # Isso permite auditoria de revogações recentes
        seven_days_ago = now - timedelta(days=7)
        
        # Buscar IDs dos tokens para deletar (limitando batch para evitar locks)
        expired_token_ids = db.query(RefreshToken.id).filter(
            or_(
                # Tokens expirados há mais de 7 dias
                and_(
                    RefreshToken.expires_at < seven_days_ago,
                    RefreshToken.revoked == False
                ),
                # Tokens revogados há mais de 7 dias (usando created_at como proxy)
                and_(
                    RefreshToken.revoked == True,
                    RefreshToken.created_at < seven_days_ago
                )
            )
        ).limit(batch_size).all()
        
        if not expired_token_ids:
            return 0
        
        # Extrair apenas os IDs
        ids = [token_id[0] for token_id in expired_token_ids]
        count = len(ids)
        
        # Deletar por IDs (mais confiável)
        db.query(RefreshToken).filter(
            RefreshToken.id.in_(ids)
        ).delete(synchronize_session=False)
        
        db.commit()
        return count
