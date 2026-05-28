from sqlalchemy.orm import Session
from app.domain.auth.models.email_log_model import EmailLog, EmailStatus, EmailType
from datetime import datetime, timezone
from typing import Optional, List, Dict

class EmailLogRepository:
    @staticmethod
    def create_log(
        db: Session,
        recipient_email: str,
        subject: str,
        email_type: EmailType,
        user_id: Optional[int] = None,
        status: EmailStatus = EmailStatus.PENDING,
        extra_data: Optional[Dict] = None
    ) -> EmailLog:
        log = EmailLog(
            user_id=user_id,
            recipient_email=recipient_email,
            subject=subject,
            email_type=email_type,
            status=status,
            extra_data=extra_data or {}
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def update_log_status(
        db: Session,
        log_id: int,
        status: EmailStatus,
        error_message: Optional[str] = None,
        smtp_response: Optional[str] = None,
        server_response: Optional[str] = None,
        external_id: Optional[str] = None,
        message_id: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None
    ) -> Optional[EmailLog]:
        log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if log:
            log.status = status
            if status == EmailStatus.SENT:
                log.sent_at = datetime.now(timezone.utc)
            if error_message:
                log.error_message = error_message
            if smtp_response:
                log.smtp_response = smtp_response
            if server_response:
                log.server_response = server_response
            if external_id:
                log.external_id = external_id
            if message_id:
                log.message_id = message_id
            if smtp_host:
                log.smtp_host = smtp_host
            if smtp_port:
                log.smtp_port = smtp_port
            db.commit()
            db.refresh(log)
        return log
    
    @staticmethod
    def update_delivery_status(
        db: Session,
        log_id: int,
        status: EmailStatus,
        external_id: Optional[str] = None
    ) -> Optional[EmailLog]:
        log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if log:
            log.status = status
            log.delivered_at = datetime.now(timezone.utc)
            if external_id:
                log.external_id = external_id
            db.commit()
            db.refresh(log)
        return log
    
    @staticmethod
    def mark_opened(
        db: Session,
        log_id: int,
        opened_at: Optional[datetime] = None
    ) -> Optional[EmailLog]:
        log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if log:
            if log.status != EmailStatus.CLICKED:  # Não sobrescrever clicked
                log.status = EmailStatus.OPENED
            log.opened_at = opened_at or datetime.now(timezone.utc)
            db.commit()
            db.refresh(log)
        return log
    
    @staticmethod
    def mark_clicked(
        db: Session,
        log_id: int,
        clicked_at: Optional[datetime] = None
    ) -> Optional[EmailLog]:
        log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if log:
            log.status = EmailStatus.CLICKED
            log.clicked_at = clicked_at or datetime.now(timezone.utc)
            db.commit()
            db.refresh(log)
        return log
    
    @staticmethod
    def update_validation_info(
        db: Session,
        log_id: int,
        email_validated: bool,
        validation_errors: Optional[str] = None,
        mx_server: Optional[str] = None
    ) -> Optional[EmailLog]:
        log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if log:
            log.email_validated = email_validated
            if validation_errors:
                log.validation_errors = validation_errors
            if mx_server:
                log.mx_server = mx_server
            db.commit()
            db.refresh(log)
        return log
    
    @staticmethod
    def get_logs_by_email(
        db: Session,
        email: str,
        limit: int = 50
    ) -> List[EmailLog]:
        return db.query(EmailLog)\
            .filter(EmailLog.recipient_email == email)\
            .order_by(EmailLog.created_at.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_logs_by_user(
        db: Session,
        user_id: int,
        limit: int = 50
    ) -> List[EmailLog]:
        return db.query(EmailLog)\
            .filter(EmailLog.user_id == user_id)\
            .order_by(EmailLog.created_at.desc())\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_log_by_id(db: Session, log_id: int) -> Optional[EmailLog]:
        return db.query(EmailLog).filter(EmailLog.id == log_id).first()
    
    @staticmethod
    def get_recent_logs(
        db: Session,
        limit: int = 100,
        email_type: Optional[EmailType] = None,
        status: Optional[EmailStatus] = None
    ) -> List[EmailLog]:
        query = db.query(EmailLog)
        if email_type:
            query = query.filter(EmailLog.email_type == email_type)
        if status:
            query = query.filter(EmailLog.status == status)
        return query.order_by(EmailLog.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_email_proof(
        db: Session,
        email: str,
        email_type: Optional[EmailType] = None
    ) -> List[Dict]:
        """
        Retorna prova completa de envio de emails para um destinatário
        Útil para mostrar ao cliente que o email foi enviado
        """
        query = db.query(EmailLog).filter(EmailLog.recipient_email == email)
        
        if email_type:
            query = query.filter(EmailLog.email_type == email_type)
        
        logs = query.order_by(EmailLog.created_at.desc()).all()
        
        return [
            {
                "id": log.id,
                "email": log.recipient_email,
                "subject": log.subject,
                "type": log.email_type.value if log.email_type else None,
                "status": log.status.value if log.status else None,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
                "delivered_at": log.delivered_at.isoformat() if log.delivered_at else None,
                "opened_at": log.opened_at.isoformat() if log.opened_at else None,
                "clicked_at": log.clicked_at.isoformat() if log.clicked_at else None,
                "smtp_response": log.smtp_response,
                "error_message": log.error_message,
                "message_id": log.message_id,
                "external_id": log.external_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]

