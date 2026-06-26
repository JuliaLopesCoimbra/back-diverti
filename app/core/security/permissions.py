from fastapi import Depends, HTTPException, status
from app.domain.auth.models.user_model import User
from app.core.security.auth_dependency import get_current_user


class PermissionChecker:
    """Sistema de verificação de permissões baseado em roles"""

    @staticmethod
    def is_admin_master(user: User) -> bool:
        return user.role == "admin_master"

    @staticmethod
    def is_admin(user: User) -> bool:
        return user.role == "admin"

    @staticmethod
    def is_patrocinador(user: User) -> bool:
        return user.role == "patrocinador"

    @staticmethod
    def is_admin_master_or_admin(user: User) -> bool:
        return user.role in ["admin_master", "admin"]

    @staticmethod
    def can_invite_admin(user: User) -> bool:
        """Apenas admin_master pode convidar admin"""
        return user.role == "admin_master"

    @staticmethod
    def can_invite_patrocinador(user: User) -> bool:
        """Admin_master e admin podem convidar patrocinador"""
        return user.role in ["admin_master", "admin"]

    @staticmethod
    def can_create_event(user: User) -> bool:
        """Admin_master e admin podem criar eventos"""
        return user.role in ["admin_master", "admin"]

    @staticmethod
    def can_create_post(user: User) -> bool:
        """Admin_master, admin e patrocinador podem criar posts"""
        return user.role in ["admin_master", "admin", "patrocinador"]

    @staticmethod
    def can_approve_post(user: User) -> bool:
        """Apenas admin_master e admin podem aprovar posts"""
        return user.role in ["admin_master", "admin"]

    @staticmethod
    def can_manage_patrocinador(user: User, patrocinador: User) -> bool:
        """Admin_master e admin podem gerenciar patrocinadores"""
        if user.role == "admin_master":
            return True
        if user.role == "admin":
            # Admin só pode gerenciar patrocinadores que ele convidou
            return patrocinador.invited_by_id == user.id
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


def require_admin_or_master(user: User = Depends(get_current_user)):
    """Admin_master ou admin podem acessar"""
    if not PermissionChecker.is_admin_master_or_admin(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem acessar este recurso."
        )
    return user


def require_patrocinador_or_above(user: User = Depends(get_current_user)):
    """Patrocinador, admin ou admin_master podem acessar"""
    if not PermissionChecker.can_create_post(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas patrocinadores, admins ou admin master podem acessar este recurso."
        )
    return user


def require_operador_or_above(user: User = Depends(get_current_user)):
    """Operador, admin ou admin_master podem acessar (rotas de cozinha/garçom)"""
    if user.role not in ("operador", "admin", "admin_master"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito à equipe de operação."
        )
    return user
