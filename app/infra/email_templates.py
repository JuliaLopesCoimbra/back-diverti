from app.config.settings import settings
from datetime import datetime

class EmailTemplates:
    """Templates profissionais para emails transacionais"""
    
    # URL do logo - usando CloudFront ou URL do frontend
    # Você pode ajustar isso para apontar para onde o logo está hospedado
    @staticmethod
    def get_logo_url() -> str:
        """Retorna a URL do logo, priorizando CloudFront"""
        if hasattr(settings, 'AWS_CLOUDFRONT_DOMAIN') and settings.AWS_CLOUDFRONT_DOMAIN:
            return f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/email/logo-n1.png"
        return f"{settings.FRONTEND_URL}/logo/logo-n1.png"
    
    @staticmethod
    def get_base_template(content: str, primary_color: str = "#6366f1") -> str:
        """Template base com header e footer"""
        current_year = datetime.now().year
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>N1 App</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f3f4f6; padding: 20px 0;">
        <tr>
            <td align="center">
                <table role="presentation" style="width: 600px; max-width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header com Logo -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {primary_color} 0%, #4f46e5 100%); padding: 40px 30px; text-align: center;">
                            <img src="{EmailTemplates.get_logo_url()}" alt="N1 App Logo" style="max-width: 150px; height: auto; display: block; margin: 0 auto;" />
                        </td>
                    </tr>
                    
                    <!-- Conteúdo -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            {content}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 14px; line-height: 1.5;">
                                <strong style="color: #111827;">N1 App</strong>
                            </p>
                            <p style="margin: 0; color: #9ca3af; font-size: 12px; line-height: 1.5;">
                                Este é um email automático, por favor não responda.
                            </p>
                            <p style="margin: 15px 0 0 0; color: #9ca3af; font-size: 12px; line-height: 1.5;">
                                © {current_year} {settings.APP_NAME} - Todos os direitos reservados
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
    
    @staticmethod
    def verification_email(user_name: str, verification_link: str) -> str:
        """Template para email de verificação"""
        content = f"""
            <h1 style="margin: 0 0 20px 0; color: #111827; font-size: 24px; font-weight: 600; line-height: 1.3;">
                Confirme seu e-mail
            </h1>
            
            <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                Olá <strong style="color: #111827;">{user_name}</strong>,
            </p>
            
            <p style="margin: 0 0 30px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                Obrigado por se cadastrar no N1 App! Para completar seu cadastro e começar a usar nossa plataforma, 
                precisamos confirmar seu endereço de e-mail.
            </p>
            
            <table role="presentation" style="width: 100%; margin: 30px 0;">
                <tr>
                    <td align="center">
                        <a href="{verification_link}" 
                           style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); 
                                  color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; 
                                  font-size: 16px; box-shadow: 0 4px 6px rgba(99, 102, 241, 0.3);">
                            Confirmar E-mail
                        </a>
                    </td>
                </tr>
            </table>
            
            <p style="margin: 30px 0 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
            </p>
            
            <p style="margin: 10px 0 0 0; color: #6366f1; font-size: 14px; line-height: 1.6; word-break: break-all;">
                <a href="{verification_link}" style="color: #6366f1; text-decoration: underline;">{verification_link}</a>
            </p>
            
            <p style="margin: 30px 0 0 0; color: #9ca3af; font-size: 12px; line-height: 1.6; border-top: 1px solid #e5e7eb; padding-top: 20px;">
                <strong>Importante:</strong> Este link expira em 24 horas. Se você não solicitou este e-mail, 
                pode ignorá-lo com segurança.
            </p>
        """
        return EmailTemplates.get_base_template(content, "#6366f1")
    
    @staticmethod
    def password_reset_email(reset_link: str) -> str:
        """Template para email de recuperação de senha"""
        content = f"""
            <h1 style="margin: 0 0 20px 0; color: #111827; font-size: 24px; font-weight: 600; line-height: 1.3;">
                Recuperação de Senha
            </h1>
            
            <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                Olá,
            </p>
            
            <p style="margin: 0 0 30px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                Recebemos uma solicitação para redefinir a senha da sua conta no N1 App. 
                Clique no botão abaixo para criar uma nova senha.
            </p>
            
            <table role="presentation" style="width: 100%; margin: 30px 0;">
                <tr>
                    <td align="center">
                        <a href="{reset_link}" 
                           style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                                  color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; 
                                  font-size: 16px; box-shadow: 0 4px 6px rgba(239, 68, 68, 0.3);">
                            Redefinir Senha
                        </a>
                    </td>
                </tr>
            </table>
            
            <p style="margin: 30px 0 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
            </p>
            
            <p style="margin: 10px 0 0 0; color: #ef4444; font-size: 14px; line-height: 1.6; word-break: break-all;">
                <a href="{reset_link}" style="color: #ef4444; text-decoration: underline;">{reset_link}</a>
            </p>
            
            <p style="margin: 30px 0 0 0; color: #9ca3af; font-size: 12px; line-height: 1.6; border-top: 1px solid #e5e7eb; padding-top: 20px;">
                <strong>Importante:</strong> Este link expira em 1 hora. Se você não solicitou a recuperação de senha, 
                ignore este e-mail e sua senha permanecerá inalterada.
            </p>
        """
        return EmailTemplates.get_base_template(content, "#ef4444")
    
    @staticmethod
    def first_access_email(user_name: str, access_link: str) -> str:
        """Template para email de primeiro acesso"""
        content = f"""
            <h1 style="margin: 0 0 20px 0; color: #111827; font-size: 24px; font-weight: 600; line-height: 1.3;">
                Primeiro Acesso
            </h1>
            
            <p style="margin: 0 0 20px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                Olá <strong style="color: #111827;">{user_name}</strong>,
            </p>
            
            <p style="margin: 0 0 30px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                Você foi convidado como administrador do N1 App. Clique no botão abaixo para definir sua senha 
                e acessar o sistema.
            </p>
            
            <table role="presentation" style="width: 100%; margin: 30px 0;">
                <tr>
                    <td align="center">
                        <a href="{access_link}" 
                           style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                  color: #ffffff; text-decoration: none; border-radius: 6px; font-weight: 600; 
                                  font-size: 16px; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);">
                            Definir Senha
                        </a>
                    </td>
                </tr>
            </table>
            
            <p style="margin: 30px 0 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
            </p>
            
            <p style="margin: 10px 0 0 0; color: #10b981; font-size: 14px; line-height: 1.6; word-break: break-all;">
                <a href="{access_link}" style="color: #10b981; text-decoration: underline;">{access_link}</a>
            </p>
            
            <p style="margin: 30px 0 0 0; color: #9ca3af; font-size: 12px; line-height: 1.6; border-top: 1px solid #e5e7eb; padding-top: 20px;">
                <strong>Importante:</strong> Este link expira em 24 horas. Mantenha suas credenciais em segurança.
            </p>
        """
        return EmailTemplates.get_base_template(content, "#10b981")

