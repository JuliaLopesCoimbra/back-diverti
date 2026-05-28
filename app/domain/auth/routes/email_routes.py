from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.config.auth_db import get_db
from app.domain.auth.schemas.auth_schema import ResendVerificationRequest
from app.domain.auth.schemas.email_schema import VerifyEmailRequest
from app.domain.auth.controllers.email_verification_controller import EmailVerificationController
from app.infra.redis import check_rate_limit

router = APIRouter(prefix="/auth", tags=["Email Verification"])

@router.post("/resend-verification")
def resend_verification(
    body: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    # Rate limiting: 3 tentativas por hora por IP e por email (CRÍTICO - retorna 503 se Redis cair)
    ip = request.client.host
    email = body.email.lower()
    
    # Limite por IP
    allowed_ip, _ = check_rate_limit(f"resend-verification:ip:{ip}", max_requests=3, window_seconds=3600, critical=True)
    # Limite por email
    allowed_email, _ = check_rate_limit(f"resend-verification:email:{email}", max_requests=3, window_seconds=3600, critical=True)
    
    if not allowed_ip or not allowed_email:
        raise HTTPException(
            status_code=429,
            detail="Muitas tentativas. Tente novamente em 1 hora.",
            headers={"Retry-After": "3600"}
        )
    
    return EmailVerificationController.resend_email(db, body.email)

@router.post("/verify-email")
def verify_email(body: VerifyEmailRequest, db: Session = Depends(get_db)):
    return EmailVerificationController.verify_email(db, body.token)
