from fastapi import HTTPException, status

def Unauthorized(detail="Não autorizado"):
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

def Forbidden(detail="Acesso negado"):
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
