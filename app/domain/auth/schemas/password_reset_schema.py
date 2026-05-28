from pydantic import BaseModel, EmailStr, field_validator
from app.core.security.password_validator import validate_password
from fastapi import HTTPException
from app.domain.auth.schemas.auth_schema import validate_email_tld

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_tld(v)

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        try:
            validate_password(v)
        except HTTPException as e:
            raise ValueError(e.detail)
        return v
