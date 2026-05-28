import httpx
from app.config.settings import settings

class GoogleOAuth:
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    @staticmethod
    def get_authorization_url(state: str):
        url = (
            f"{GoogleOAuth.AUTH_URL}"
            f"?client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=openid%20email%20profile"
            f"&state={state}"
        )
        return url

    @staticmethod
    def exchange_code(code: str):
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        res = httpx.post(GoogleOAuth.TOKEN_URL, data=data)
        res.raise_for_status()
        return res.json()

    @staticmethod
    def get_user_info(access_token: str):
        headers = {"Authorization": f"Bearer {access_token}"}
        res = httpx.get(GoogleOAuth.USERINFO_URL, headers=headers)
        res.raise_for_status()
        return res.json()
