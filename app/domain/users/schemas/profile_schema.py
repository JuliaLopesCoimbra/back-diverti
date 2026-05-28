from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime, date

class ProfileResponse(BaseModel):
    id: int
    name: Optional[str]
    email: str
    profile_photo: Optional[str]
    role: str
    is_email_verified: bool
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    birth_date: Optional[datetime]
    gender: Optional[str]

    class Config:
        from_attributes = True

class UpdateProfileRequest(BaseModel):
    birth_date: Optional[date] = None
    gender: Optional[Literal["male", "female", "other", "prefer_not_to_say"]] = None

    @field_validator('birth_date')
    @classmethod
    def validate_birth_date(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return v
        
        today = date.today()
        
        # Validar se a data não é muito antiga (antes de 1900)
        if v.year < 1900:
            raise ValueError("Data de nascimento inválida. Por favor, informe uma data válida.")
        
        # Validar se a data não é no futuro
        if v > today:
            raise ValueError("Data de nascimento não pode ser no futuro.")
        
        # Validar idade mínima
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError("Você deve ter pelo menos 18 anos.")
        
        # Validar idade máxima razoável (por exemplo, 150 anos)
        if age > 150:
            raise ValueError("Data de nascimento inválida. Por favor, informe uma data válida.")
        
        return v






