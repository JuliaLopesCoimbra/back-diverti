from app.domain.auth.services.email_verification_service import EmailVerificationService

class EmailVerificationController:

    @staticmethod
    def resend_email(db, email: str):
        return EmailVerificationService.resend_verification_email(db, email)

    @staticmethod
    def verify_email(db, token):
        return EmailVerificationService.verify_email(db, token)
