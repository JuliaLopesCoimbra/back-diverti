from app.domain.auth.services.password_reset_service import PasswordResetService

class PasswordResetController:

    @staticmethod
    def send_reset(db, email):
        return PasswordResetService.send_reset_email(db, email)

    @staticmethod
    def reset(db, token, new_password):
        return PasswordResetService.reset_password(db, token, new_password)
