from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.config.auth_db import get_db
from app.domain.auth.schemas.password_reset_schema import ForgotPasswordRequest, ResetPasswordRequest
from app.domain.auth.controllers.password_reset_controller import PasswordResetController
from app.infra.redis import check_rate_limit

router = APIRouter(prefix="/auth", tags=["Password Reset"])

@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)):
    # Rate limiting: 3 tentativas por hora por IP e por email (CRÍTICO - retorna 503 se Redis cair)
    ip = request.client.host
    email = body.email.lower()
    
    # Limite por IP
    allowed_ip, _ = check_rate_limit(f"forgot-password:ip:{ip}", max_requests=10, window_seconds=3600, critical=True)
    # Limite por email
    allowed_email, _ = check_rate_limit(f"forgot-password:email:{email}", max_requests=3, window_seconds=3600, critical=True)
    
    if not allowed_ip or not allowed_email:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas. Tente novamente em 1 hora.",
            headers={"Retry-After": "3600"}
        )
    
    return PasswordResetController.send_reset(db, body.email)


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    return PasswordResetController.reset(db, body.token, body.new_password)
