import re
from fastapi import HTTPException

def validate_password(password: str) -> None:
    """
    Valida se a senha atende aos requisitos:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="A senha deve ter no mínimo 8 caracteres."
        )
    
    if not re.search(r'[A-Z]', password):
        raise HTTPException(
            status_code=400,
            detail="A senha deve conter pelo menos uma letra maiúscula."
        )
    
    if not re.search(r'[a-z]', password):
        raise HTTPException(
            status_code=400,
            detail="A senha deve conter pelo menos uma letra minúscula."
        )
    
    if not re.search(r'\d', password):
        raise HTTPException(
            status_code=400,
            detail="A senha deve conter pelo menos um número."
        )
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        raise HTTPException(
            status_code=400,
            detail="A senha deve conter pelo menos um caractere especial (!@#$%^&*()_+-=[]{}|;:,.<>/?)."
        )




















