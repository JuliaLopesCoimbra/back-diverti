from fastapi import Depends, HTTPException, status
from app.domain.auth.models.user_model import User
from app.core.security.auth_dependency import get_current_user


class PermissionChecker:
    """Sistema de verificação de permissões baseado em roles"""
    
    @staticmethod
    def is_admin_master(user: User) -> bool:
        return user.role == "admin_master"
    
    @staticmethod
    def is_subadmin(user: User) -> bool:
        return user.role == "subadmin"
    
    @staticmethod
    def is_colunista(user: User) -> bool:
        return user.role == "colunista"
    
    @staticmethod
    def is_admin_master_or_subadmin(user: User) -> bool:
        return user.role in ["admin_master", "subadmin"]

    @staticmethod
    def is_admin_or_master(user: User) -> bool:
        return user.role in ["admin_master", "admin"]
    
    @staticmethod
    def can_invite_subadmin(user: User) -> bool:
        """Apenas admin_master pode convidar subadmin"""
        return user.role == "admin_master"
    
    @staticmethod
    def can_invite_colunista(user: User) -> bool:
        """Admin_master e subadmin podem convidar colunista"""
        return user.role in ["admin_master", "subadmin"]
    
    @staticmethod
    def can_create_event(user: User) -> bool:
        """Admin_master e subadmin podem criar eventos"""
        return user.role in ["admin_master", "subadmin"]
    
    @staticmethod
    def can_create_post(user: User) -> bool:
        """Admin_master, subadmin e colunista podem criar posts"""
        return user.role in ["admin_master", "subadmin", "colunista"]
    
    @staticmethod
    def can_approve_post(user: User) -> bool:
        """Apenas admin_master e subadmin podem aprovar posts"""
        return user.role in ["admin_master", "subadmin"]
    
    @staticmethod
    def can_manage_colunista(user: User, colunista: User) -> bool:
        """Admin_master e subadmin podem gerenciar colunistas"""
        if user.role == "admin_master":
            return True
        if user.role == "subadmin":
            # Subadmin só pode gerenciar colunistas que ele convidou
            return colunista.invited_by_id == user.id
        return False


# Dependencies para usar nas rotas
def require_admin_master(user: User = Depends(get_current_user)):
    """Apenas admin_master pode acessar"""
    if not PermissionChecker.is_admin_master(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas o administrador master pode acessar este recurso."
        )
    return user


def require_subadmin_or_master(user: User = Depends(get_current_user)):
    """Admin_master ou subadmin podem acessar"""
    if not PermissionChecker.is_admin_master_or_subadmin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem acessar este recurso."
        )
    return user


def require_admin_or_master(user: User = Depends(get_current_user)):
    """Admin compatível ou admin_master podem acessar"""
    if not PermissionChecker.is_admin_or_master(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas admin ou admin master podem acessar este recurso."
        )
    return user


def require_colunista_or_above(user: User = Depends(get_current_user)):
    """Colunista, subadmin ou admin_master podem acessar"""
    if not PermissionChecker.can_create_post(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas colunistas, subadmins ou admin master podem acessar este recurso."
        )
    return user

