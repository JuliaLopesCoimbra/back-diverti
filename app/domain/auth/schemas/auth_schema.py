from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal, Optional
from datetime import datetime, date
from app.core.security.password_validator import validate_password
from app.core.security.cpf_validator import validate_cpf
from fastapi import HTTPException
import re

# Lista de TLDs válidos comuns (incluindo os mais usados)
VALID_TLDS = {
    'com', 'org', 'net', 'edu', 'gov', 'mil', 'int', 'br', 'co', 'uk', 'us', 'ca', 'au', 'de', 'fr', 'it', 'es', 'pt', 
    'nl', 'be', 'ch', 'at', 'se', 'no', 'dk', 'fi', 'pl', 'cz', 'ie', 'gr', 'ru', 'jp', 'cn', 'in', 'kr', 'mx', 'ar',
    'cl', 'co', 'pe', 've', 'ec', 'uy', 'py', 'bo', 'cr', 'pa', 'do', 'gt', 'hn', 'ni', 'sv', 'com.br', 'com.mx',
    'com.ar', 'com.co', 'org.br', 'net.br', 'gov.br', 'edu.br', 'info', 'biz', 'name', 'pro', 'aero', 'coop', 'museum',
    'io', 'dev', 'tech', 'online', 'site', 'website', 'xyz', 'app', 'cloud', 'store', 'shop', 'blog', 'news', 'tv',
    'me', 'cc', 'ws', 'mobi', 'asia', 'tel', 'jobs', 'travel', 'cat', 'jobs', 'xxx', 'post', 'asia', 'eu', 'ac', 'ad',
    'ae', 'af', 'ag', 'ai', 'al', 'am', 'ao', 'aq', 'as', 'aw', 'ax', 'az', 'ba', 'bb', 'bd', 'bf', 'bg', 'bh', 'bi',
    'bj', 'bm', 'bn', 'bs', 'bt', 'bv', 'bw', 'by', 'bz', 'cd', 'cf', 'cg', 'ci', 'ck', 'cm', 'cn', 'cu', 'cv', 'cw',
    'cx', 'cy', 'dj', 'dm', 'do', 'dz', 'ee', 'eg', 'eh', 'er', 'et', 'fj', 'fk', 'fm', 'fo', 'ga', 'gb', 'gd', 'ge',
    'gf', 'gg', 'gh', 'gi', 'gl', 'gm', 'gn', 'gp', 'gq', 'gs', 'gt', 'gu', 'gw', 'gy', 'hk', 'hm', 'hn', 'hr', 'ht',
    'hu', 'id', 'il', 'im', 'iq', 'ir', 'is', 'je', 'jm', 'jo', 'ke', 'kg', 'kh', 'ki', 'km', 'kn', 'kp', 'kw', 'ky',
    'kz', 'la', 'lb', 'lc', 'li', 'lk', 'lr', 'ls', 'lt', 'lu', 'lv', 'ly', 'ma', 'mc', 'md', 'me', 'mf', 'mg', 'mh',
    'mk', 'ml', 'mm', 'mn', 'mo', 'mp', 'mq', 'mr', 'ms', 'mt', 'mu', 'mv', 'mw', 'my', 'mz', 'na', 'nc', 'ne', 'nf',
    'ng', 'ni', 'np', 'nr', 'nu', 'nz', 'om', 'pa', 'pe', 'pf', 'pg', 'ph', 'pk', 'pm', 'pn', 'pr', 'ps', 'pw', 'qa',
    're', 'ro', 'rs', 'rw', 'sa', 'sb', 'sc', 'sd', 'sg', 'sh', 'si', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'ss',
    'st', 'sv', 'sx', 'sy', 'sz', 'tc', 'td', 'tf', 'tg', 'th', 'tj', 'tk', 'tl', 'tm', 'tn', 'to', 'tr', 'tt', 'tv',
    'tw', 'tz', 'ua', 'ug', 'um', 'uy', 'uz', 'va', 'vc', 've', 'vg', 'vi', 'vn', 'vu', 'wf', 'ye', 'yt', 'za', 'zm', 'zw'
}

def validate_full_name(name: str) -> str:
    """
    Valida se o nome é um nome completo válido (nome e sobrenome).
    """
    if not name or not name.strip():
        raise ValueError("Por favor, informe seu nome completo.")
    
    trimmed_name = name.strip()
    
    # Verificar se tem pelo menos 3 caracteres
    if len(trimmed_name) < 3:
        raise ValueError("Nome deve ter pelo menos 3 caracteres.")
    
    # Verificar se tem pelo menos nome e sobrenome (2 palavras)
    name_parts = [part for part in trimmed_name.split() if part]
    if len(name_parts) < 2:
        raise ValueError("Por favor, informe seu nome completo (nome e sobrenome).")
    
    # Verificar se cada parte tem pelo menos 2 caracteres
    for part in name_parts:
        if len(part) < 2:
            raise ValueError("Cada parte do nome deve ter pelo menos 2 caracteres.")
    
    # Verificar se contém apenas letras, espaços, hífens e acentos
    import re
    if not re.match(r"^[a-zA-ZÀ-ÿ\s'-]+$", trimmed_name):
        raise ValueError("Nome inválido. Use apenas letras, espaços, hífens e acentos.")
    
    # Verificar se não contém caracteres especiais como @, números, etc.
    if re.search(r"[@#$%^&*()_+=\[\]{}|\\:\";'<>?,.\/0-9]", trimmed_name):
        raise ValueError("Nome inválido. Não é permitido usar caracteres especiais ou números.")
    
    return trimmed_name

def validate_email_tld(email: str) -> str:
    """
    Valida se o email tem um TLD válido.
    """
    # Extrair o domínio do email
    if '@' not in email:
        raise ValueError("Email inválido.")
    
    domain = email.split('@')[1]
    
    # Verificar se tem pelo menos um ponto (para separar domínio de TLD)
    if '.' not in domain:
        raise ValueError("Email inválido. Domínio deve ter uma extensão válida (ex: .com, .br).")
    
    # Extrair o TLD (última parte após o último ponto)
    parts = domain.split('.')
    tld = parts[-1].lower()
    
    # Verificar se o TLD tem pelo menos 2 caracteres
    if len(tld) < 2:
        raise ValueError("Email inválido. Extensão do domínio deve ter pelo menos 2 caracteres.")
    
    # Verificar se o TLD contém apenas letras
    if not tld.isalpha():
        raise ValueError("Email inválido. Extensão do domínio deve conter apenas letras.")
    
    # Verificar TLDs de dois níveis (ex: com.br, co.uk)
    if len(parts) >= 2:
        two_level_tld = f"{parts[-2]}.{parts[-1]}".lower()
        if two_level_tld in VALID_TLDS:
            return email
    
    # Verificar TLD de um nível
    if tld not in VALID_TLDS:
        raise ValueError("Email inválido. Por favor, informe um email com extensão válida (ex: .com, .br, .org).")
    
    return email

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    birth_date: date
    cpf: str
    gender: Literal["male", "female", "other", "prefer_not_to_say"]
    lgpd_accepted: bool
    age_terms_accepted: bool
    marketing_email_accepted: bool = False

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_full_name(v)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_tld(v)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        try:
            validate_password(v)
        except HTTPException as e:
            raise ValueError(e.detail)
        return v
    
    @field_validator('birth_date')
    @classmethod
    def validate_age(cls, v: date) -> date:
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
            raise ValueError("Você deve ter pelo menos 18 anos para se cadastrar.")
        
        # Validar idade máxima razoável (por exemplo, 150 anos)
        if age > 150:
            raise ValueError("Data de nascimento inválida. Por favor, informe uma data válida.")
        
        return v
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf_field(cls, v: str) -> str:
        try:
            return validate_cpf(v)
        except ValueError as e:
            raise ValueError(str(e))
    
    @field_validator('lgpd_accepted', 'age_terms_accepted')
    @classmethod
    def validate_terms_accepted(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Você deve aceitar os termos para continuar.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_tld(v)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class AdminCreateAdminRequest(BaseModel):
    name: str
    email: EmailStr
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_full_name(v)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_tld(v)

class InviteAdminRequest(BaseModel):
    name: str
    email: EmailStr
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_full_name(v)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_tld(v)

class FirstAccessRequest(BaseModel):
    token: str
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        try:
            validate_password(v)
        except HTTPException as e:
            raise ValueError(e.detail)
        return v

class ResendVerificationRequest(BaseModel):
    email: EmailStr
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_tld(v)

class ResendAdminInviteRequest(BaseModel):
    email: EmailStr
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_tld(v)

class InvitePatrocinadorRequest(BaseModel):
    name: str
    email: EmailStr

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        return validate_full_name(v)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_tld(v)

class AgeVerificationRequest(BaseModel):
    confirmed: bool = True
    birth_date: date

    @field_validator('birth_date')
    @classmethod
    def validate_age(cls, v: date) -> date:
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
            raise ValueError("Você deve ter pelo menos 18 anos para usar este serviço.")
        
        # Validar idade máxima razoável (por exemplo, 150 anos)
        if age > 150:
            raise ValueError("Data de nascimento inválida. Por favor, informe uma data válida.")
        
        return v

class UserInfo(BaseModel):
    """Informações básicas de um usuário"""
    id: int
    name: Optional[str]
    email: str

    class Config:
        from_attributes = True

class CompleteProfileRequest(BaseModel):
    cpf: str
    gender: Literal["male", "female", "other", "prefer_not_to_say"]
    lgpd_accepted: bool
    age_terms_accepted: bool
    marketing_email_accepted: bool = False

    @field_validator('cpf')
    @classmethod
    def validate_cpf_field(cls, v: str) -> str:
        try:
            return validate_cpf(v)
        except ValueError as e:
            raise ValueError(str(e))
    
    @field_validator('lgpd_accepted', 'age_terms_accepted')
    @classmethod
    def validate_terms_accepted(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Você deve aceitar os termos para continuar.")
        return v

class CompleteEmailRequest(BaseModel):
    email: EmailStr

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Verificar se não é um email temporário
        if "@facebook.user" in v or "@facebook.temp" in v or "@instagram.user" in v:
            raise ValueError("Por favor, informe um email válido.")
        return validate_email_tld(v)

class CompleteEmailResponse(BaseModel):
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    requires_age_verification: Optional[bool] = None
    requires_profile_completion: Optional[bool] = None
    requires_email_verification: Optional[bool] = None
    temp_token: Optional[str] = None
    email: Optional[str] = None

class UpdateEmailByCpfRequest(BaseModel):
    cpf: str
    email: EmailStr

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        return validate_email_tld(v)

    @field_validator('cpf')
    @classmethod
    def validate_cpf_field(cls, v: str) -> str:
        try:
            return validate_cpf(v)
        except ValueError as e:
            raise ValueError(str(e))

class UpdateEmailByCpfResponse(BaseModel):
    message: str

class UserResponse(BaseModel):
    id: int
    name: Optional[str]
    email: str
    role: str
    status: str
    invited_by_id: Optional[int]
    invited_by: Optional[UserInfo] = None
    deactivated_by_id: Optional[int]
    deactivated_by: Optional[UserInfo] = None
    deactivated_at: Optional[datetime]
    reactivated_by_id: Optional[int]
    reactivated_by: Optional[UserInfo] = None
    reactivated_at: Optional[datetime]
    created_at: datetime
    is_email_verified: bool

    class Config:
        from_attributes = True