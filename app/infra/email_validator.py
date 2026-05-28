import re
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class EmailValidator:
    """
    Validação de email em múltiplos níveis:
    1. Formato (regex)
    2. Domínio existe e tem registros MX (opcional, requer dnspython)
    """
    
    @staticmethod
    def validate_format(email: str) -> Tuple[bool, Optional[str]]:
        """Valida formato básico do email"""
        if not email or not isinstance(email, str):
            return False, "Email inválido"
        
        email = email.strip().lower()
        
        # Regex mais rigoroso
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Formato de email inválido"
        
        # Verificar comprimento
        if len(email) > 254:  # RFC 5321
            return False, "Email muito longo"
        
        # Verificar partes
        parts = email.split('@')
        if len(parts) != 2:
            return False, "Formato de email inválido"
        
        local, domain = parts
        
        if len(local) > 64:  # RFC 5321
            return False, "Parte local do email muito longa"
        
        if len(domain) > 253:
            return False, "Domínio muito longo"
        
        return True, None
    
    @staticmethod
    def validate_domain_mx(email: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verifica se o domínio tem registros MX (Mail Exchange)
        Retorna: (válido, erro, servidor_mx)
        Requer: dnspython instalado (opcional)
        """
        try:
            import dns.resolver  # type: ignore
        except ImportError:
            logger.warning("dnspython não instalado. Validação MX desabilitada. Instale com: pip install dnspython")
            return True, None, None  # Retorna válido se não puder validar
        
        try:
            # Extrair domínio
            domain = email.split('@')[1]
            
            # Tentar resolver MX records
            try:
                mx_records = dns.resolver.resolve(domain, 'MX')
                mx_servers = [str(mx.exchange).rstrip('.') for mx in mx_records]
                
                if not mx_servers:
                    return False, f"Domínio {domain} não possui servidores de email (MX)", None
                
                # Ordenar por prioridade
                mx_prioritized = sorted(
                    [(mx.preference, str(mx.exchange).rstrip('.')) for mx in mx_records],
                    key=lambda x: x[0]
                )
                
                primary_mx = mx_prioritized[0][1]
                return True, None, primary_mx
                
            except dns.resolver.NXDOMAIN:
                return False, f"Domínio {domain} não existe", None
            except dns.resolver.NoAnswer:
                # Se não tem MX, tentar A record (alguns servidores usam A)
                try:
                    a_records = dns.resolver.resolve(domain, 'A')
                    if a_records:
                        return True, None, domain  # Usa o próprio domínio
                    return False, f"Domínio {domain} não possui registros MX ou A", None
                except:
                    return False, f"Domínio {domain} não possui servidores de email", None
            except Exception as e:
                logger.warning(f"Erro ao validar MX para {domain}: {str(e)}")
                return False, f"Erro ao verificar domínio: {str(e)}", None
                
        except Exception as e:
            logger.error(f"Erro inesperado ao validar email {email}: {str(e)}")
            return False, f"Erro ao validar email: {str(e)}", None
    
    @staticmethod
    def validate_email_comprehensive(email: str, check_mx: bool = True) -> Dict:
        """
        Validação completa do email
        Retorna dict com todos os detalhes
        """
        result = {
            "email": email,
            "is_valid": False,
            "format_valid": False,
            "domain_valid": False,
            "mx_server": None,
            "errors": [],
            "warnings": []
        }
        
        # 1. Validar formato
        format_valid, format_error = EmailValidator.validate_format(email)
        result["format_valid"] = format_valid
        if not format_valid:
            result["errors"].append(format_error)
            return result
        
        # 2. Validar domínio MX (se solicitado)
        if check_mx:
            mx_valid, mx_error, mx_server = EmailValidator.validate_domain_mx(email)
            result["domain_valid"] = mx_valid
            result["mx_server"] = mx_server
            if not mx_valid:
                result["errors"].append(mx_error)
                return result
        else:
            result["domain_valid"] = True  # Assumir válido se não verificar
        
        # Se chegou aqui, email é válido
        result["is_valid"] = True
        return result

