import smtplib
from email.mime.text import MIMEText
from app.config.settings import settings
from typing import Optional

class EmailSender:

    @staticmethod
    def send_email(
        to: str, 
        subject: str, 
        html: str,
        db_session=None,
        email_log_id: Optional[int] = None
    ):
        msg = MIMEText(html, "html")
        msg["Subject"] = subject
        msg["From"] = settings.MAIL_FROM
        msg["To"] = to

        try:
            # --- CÓDIGO DO RESEND REATIVADO ---
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_TLS:
                    server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.MAIL_FROM, [to], msg.as_string())

            # --- IMPLEMENTAÇÃO GMAIL COMENTADA (PLANO B) ---
            """
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.MAIL_FROM, [to], msg.as_string())
            """
            
            result = {
                "success": True,
                "status": "sent"
            }
            
            # Atualização de Log
            if db_session and email_log_id:
                from app.domain.auth.repositories.email_log_repository import EmailLogRepository
                from app.domain.auth.models.email_log_model import EmailStatus
                EmailLogRepository.update_log_status(
                    db=db_session,
                    log_id=email_log_id,
                    status=EmailStatus.SENT,
                    smtp_response="Email aceito pelo servidor SMTP do Resend"
                )
            
            return result
            
        except Exception as e:
            result = {
                "success": False,
                "status": "failed",
                "error_message": str(e)
            }
            
            if db_session and email_log_id:
                from app.domain.auth.repositories.email_log_repository import EmailLogRepository
                from app.domain.auth.models.email_log_model import EmailStatus
                EmailLogRepository.update_log_status(
                    db=db_session,
                    log_id=email_log_id,
                    status=EmailStatus.FAILED,
                    error_message=str(e)
                )
            
            return result