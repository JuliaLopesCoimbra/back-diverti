from fastapi import Depends

from app.core.security.auth_dependency import get_current_user
from app.domain.auth.services.auth_service import AuthService

class AuthController:

    @staticmethod
    def register(db, body, user_agent: str = None, ip: str = None, current_user=None):
        return AuthService.register(db, body, user_agent, ip, current_user)

    @staticmethod
    def login(db, body, agent, ip):
        return AuthService.login(db, body, agent, ip)

    @staticmethod
    def refresh(db, token, agent, ip):
        return AuthService.refresh(db, token, agent, ip)

    @staticmethod
    def logout(db, token):
        return AuthService.logout(db, token)

    @staticmethod
    def require_user(user=Depends(get_current_user)):
        return user

    @staticmethod
    def invite_admin(db, body, current_user):
        return AuthService.invite_admin(db, body, current_user)

    @staticmethod
    def first_access(db, body):
        return AuthService.first_access(db, body.token, body.password)

    @staticmethod
    def resend_admin_invite(db, email: str, admin):
        return AuthService.resend_admin_invite(db, email)

    @staticmethod
    def invite_subadmin(db, body, admin_master):
        return AuthService.invite_subadmin(db, body, admin_master)

    @staticmethod
    def invite_colunista(db, body, inviter):
        return AuthService.invite_colunista(db, body, inviter)

    @staticmethod
    def revoke_colunista_access(db, colunista_id: int, revoker):
        return AuthService.revoke_colunista_access(db, colunista_id, revoker)

    @staticmethod
    def revoke_subadmin_access(db, subadmin_id: int, admin_master):
        return AuthService.revoke_subadmin_access(db, subadmin_id, admin_master)

    @staticmethod
    def revoke_user_access(db, user_id: int, revoker):
        return AuthService.revoke_user_access(db, user_id, revoker)

    @staticmethod
    def reactivate_colunista_access(db, colunista_id: int, reactivator):
        return AuthService.reactivate_colunista_access(db, colunista_id, reactivator)

    @staticmethod
    def reactivate_subadmin_access(db, subadmin_id: int, admin_master):
        return AuthService.reactivate_subadmin_access(db, subadmin_id, admin_master)

    @staticmethod
    def reactivate_user_access(db, user_id: int, reactivator):
        return AuthService.reactivate_user_access(db, user_id, reactivator)

    @staticmethod
    def list_subadmins(db, requester, limit: int = 50, offset: int = 0):
        return AuthService.list_subadmins(db, requester, limit, offset)

    @staticmethod
    def list_colunistas(db, requester, limit: int = 50, offset: int = 0):
        return AuthService.list_colunistas(db, requester, limit, offset)

    @staticmethod
    def list_users(db, requester, limit: int = 50, offset: int = 0):
        return AuthService.list_users(db, requester, limit, offset)

    @staticmethod
    def verify_age(db, user_id: int, body, user_agent: str = None, ip: str = None):
        return AuthService.verify_age(db, user_id, body.birth_date, body.confirmed, user_agent, ip)

    @staticmethod
    def cleanup_expired_tokens(db, batch_size: int = 5000):
        return AuthService.cleanup_expired_tokens(db, batch_size)
    
    @staticmethod
    def complete_profile(db, user_id: int, body, agent: str = None, ip: str = None):
        return AuthService.complete_profile(db, user_id, body, agent, ip)
    
    @staticmethod
    def complete_email(db, user_id: int, body, agent: str = None, ip: str = None):
        return AuthService.complete_email(db, user_id, body, agent, ip)
    
    @staticmethod
    def update_email_by_cpf(db, body, agent: str = None, ip: str = None):
        return AuthService.update_email_by_cpf(db, body.cpf, body.email, agent, ip)