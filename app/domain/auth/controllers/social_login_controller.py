from app.domain.auth.services.social_login_service import SocialLoginService

class SocialLoginController:

    @staticmethod
    def google_callback(db, code, agent, ip):
        return SocialLoginService.google_callback(db, code, agent, ip)

    @staticmethod
    def facebook_callback(db, code, agent, ip):
        return SocialLoginService.facebook_callback(db, code, agent, ip)

    @staticmethod
    def instagram_callback(db, code, agent, ip):
        return SocialLoginService.instagram_callback(db, code, agent, ip)

