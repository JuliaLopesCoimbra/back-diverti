from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.config.auth_db import get_db
from app.domain.auth.repositories.email_log_repository import EmailLogRepository
from app.domain.auth.models.email_log_model import EmailType, EmailStatus
from app.core.security.auth_dependency import get_current_user
from app.domain.auth.models.user_model import User

router = APIRouter(prefix="/admin/email-logs", tags=["Email Logs"])

@router.get("/")
def get_email_logs(
    email: Optional[str] = Query(None, description="Filtrar por email"),
    user_id: Optional[int] = Query(None, description="Filtrar por user_id"),
    email_type: Optional[str] = Query(None, description="Tipo: verification, password_reset, first_access"),
    status: Optional[str] = Query(None, description="Status: pending, sent, failed, bounced, delivered, opened, clicked"),
    limit: int = Query(100, le=500, description="Limite de resultados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Consulta logs de emails enviados (apenas para admins)"""
    
    # Verificar se é admin
    if current_user.role not in ["admin_master", "admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores podem acessar.")
    
    # Converter strings para enums se fornecidos
    email_type_enum = None
    if email_type:
        try:
            email_type_enum = EmailType[email_type.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Tipo inválido: {email_type}. Use: verification, password_reset, first_access")
    
    status_enum = None
    if status:
        try:
            status_enum = EmailStatus[status.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {status}. Use: pending, sent, failed, bounced, delivered, opened, clicked")
    
    # Buscar logs
    if email:
        logs = EmailLogRepository.get_logs_by_email(db, email, limit)
    elif user_id:
        logs = EmailLogRepository.get_logs_by_user(db, user_id, limit)
    else:
        logs = EmailLogRepository.get_recent_logs(db, limit, email_type_enum, status_enum)
    
    # Converter para dict
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "recipient_email": log.recipient_email,
                "subject": log.subject,
                "email_type": log.email_type.value if log.email_type else None,
                "status": log.status.value if log.status else None,
                "error_message": log.error_message,
                "smtp_response": log.smtp_response,
                "server_response": log.server_response,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
                "delivered_at": log.delivered_at.isoformat() if log.delivered_at else None,
                "opened_at": log.opened_at.isoformat() if log.opened_at else None,
                "clicked_at": log.clicked_at.isoformat() if log.clicked_at else None,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "message_id": log.message_id,
                "external_id": log.external_id,
                "smtp_host": log.smtp_host,
                "smtp_port": log.smtp_port,
                "email_validated": log.email_validated,
                "validation_errors": log.validation_errors,
                "mx_server": log.mx_server,
                "extra_data": log.extra_data,
            }
            for log in logs
        ],
        "total": len(logs)
    }

@router.get("/proof/{email}")
def get_email_proof(
    email: str,
    email_type: Optional[str] = Query(None, description="Tipo: verification, password_reset, first_access"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna prova completa de envios para um email específico
    Útil para mostrar ao cliente que emails foram enviados
    """
    if current_user.role not in ["admin_master", "admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores podem acessar.")
    
    email_type_enum = None
    if email_type:
        try:
            email_type_enum = EmailType[email_type.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Tipo inválido: {email_type}")
    
    proof = EmailLogRepository.get_email_proof(db, email, email_type_enum)
    
    # Calcular estatísticas
    total = len(proof)
    sent = len([e for e in proof if e["status"] == "sent"])
    delivered = len([e for e in proof if e["status"] == "delivered"])
    opened = len([e for e in proof if e["status"] == "opened"])
    clicked = len([e for e in proof if e["status"] == "clicked"])
    failed = len([e for e in proof if e["status"] == "failed"])
    bounced = len([e for e in proof if e["status"] == "bounced"])
    
    return {
        "email": email,
        "total_emails": total,
        "emails": proof,
        "summary": {
            "sent": sent,
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "failed": failed,
            "bounced": bounced,
        }
    }

@router.get("/{log_id}")
def get_email_log_by_id(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna detalhes de um log específico"""
    if current_user.role not in ["admin_master", "admin"]:
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores podem acessar.")
    
    log = EmailLogRepository.get_log_by_id(db, log_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="Log não encontrado.")
    
    return {
        "id": log.id,
        "user_id": log.user_id,
        "recipient_email": log.recipient_email,
        "subject": log.subject,
        "email_type": log.email_type.value if log.email_type else None,
        "status": log.status.value if log.status else None,
        "error_message": log.error_message,
        "smtp_response": log.smtp_response,
        "server_response": log.server_response,
        "sent_at": log.sent_at.isoformat() if log.sent_at else None,
        "delivered_at": log.delivered_at.isoformat() if log.delivered_at else None,
        "opened_at": log.opened_at.isoformat() if log.opened_at else None,
        "clicked_at": log.clicked_at.isoformat() if log.clicked_at else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "message_id": log.message_id,
        "external_id": log.external_id,
        "smtp_host": log.smtp_host,
        "smtp_port": log.smtp_port,
        "email_validated": log.email_validated,
        "validation_errors": log.validation_errors,
        "mx_server": log.mx_server,
        "metadata": log.metadata,
    }

