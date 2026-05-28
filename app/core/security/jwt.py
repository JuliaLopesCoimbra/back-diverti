from datetime import datetime, timedelta
import jwt
from app.config.settings import settings

class JWTHandler:
    @staticmethod
    def create_access_token(data: dict, expires_minutes=15):
        payload = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        payload.update({"exp": expire})
        return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    @staticmethod
    def create_refresh_token(data: dict, expires_days=30):
        payload = data.copy()
        expire = datetime.utcnow() + timedelta(days=expires_days)
        payload.update({"exp": expire})
        return jwt.encode(payload, settings.JWT_REFRESH_SECRET, algorithm="HS256")

    @staticmethod
    def decode_token(token: str, refresh=False):
        secret = (
            settings.JWT_REFRESH_SECRET if refresh
            else settings.JWT_SECRET
        )
        return jwt.decode(token, secret, algorithms=["HS256"])
