import httpx
from app.config.settings import settings

class FacebookOAuth:
    AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
    USERINFO_URL = "https://graph.facebook.com/me"

    @staticmethod
    def get_authorization_url(state: str):
        url = (
            f"{FacebookOAuth.AUTH_URL}"
            f"?client_id={settings.FB_CLIENT_ID}"
            f"&redirect_uri={settings.FB_REDIRECT_URI}"
            f"&state={state}"
            f"&response_type=code"
            f"&scope=email,public_profile"
            f"&auth_type=rerequest"  # Força nova solicitação de permissões se já negou antes
        )
        return url

    @staticmethod
    def exchange_code(code: str):
        params = {
            "client_id": settings.FB_CLIENT_ID,
            "client_secret": settings.FB_CLIENT_SECRET,
            "redirect_uri": settings.FB_REDIRECT_URI,
            "code": code
        }

        res = httpx.get(FacebookOAuth.TOKEN_URL, params=params)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_user_info(access_token: str):
        import logging
        logger = logging.getLogger(__name__)
        
        params = {
            "fields": "id,name,email,picture",
            "access_token": access_token
        }
        res = httpx.get(FacebookOAuth.USERINFO_URL, params=params)
        res.raise_for_status()
        data = res.json()
        
        # Log detalhado para debug
        logger.info(f"Facebook API Response Status: {res.status_code}")
        logger.info(f"Facebook API Response Data: {data}")
        
        # Verificar se há erro na resposta do Facebook
        if "error" in data:
            error_info = data.get("error", {})
            error_msg = error_info.get("message", "Erro desconhecido do Facebook")
            error_type = error_info.get("type", "Unknown")
            error_code = error_info.get("code", "Unknown")
            logger.error(f"Facebook API Error - Type: {error_type}, Code: {error_code}, Message: {error_msg}")
            raise Exception(f"Erro ao obter informações do usuário: {error_msg}")
        
        # Verificar se email está presente
        if "email" not in data:
            logger.warning(f"Email não encontrado na resposta do Facebook. Campos retornados: {list(data.keys())}")
            # Tentar verificar permissões do token
            try:
                debug_params = {
                    "input_token": access_token,
                    "access_token": access_token
                }
                debug_res = httpx.get("https://graph.facebook.com/debug_token", params=debug_params)
                if debug_res.status_code == 200:
                    debug_data = debug_res.json()
                    logger.info(f"Facebook Debug Token Info: {debug_data}")
                    if "data" in debug_data:
                        scopes = debug_data.get("data", {}).get("scopes", [])
                        logger.info(f"Scopes concedidos pelo usuário: {scopes}")
            except Exception as e:
                logger.warning(f"Erro ao verificar token debug: {e}")
        
        return data
