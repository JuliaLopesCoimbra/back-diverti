import base64
import hashlib
import json
from typing import Optional

from app.config.settings import settings


def _sign(payload: str) -> str:
    signature = hashlib.sha256(f"{settings.JWT_SECRET}{payload}".encode()).digest()
    return base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")


def _encode_payload(payload: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode()).rstrip(b"=").decode("ascii")


def create_camping_booking_token(booking_id: int, user_id: int, camping_session_id: int) -> str:
    payload = _encode_payload(
        {
            "b": booking_id,
            "u": user_id,
            "c": camping_session_id,
        }
    )
    return f"{payload}.{_sign(payload)}"


def read_camping_booking_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None

        payload_b64, signature = parts
        if _sign(payload_b64) != signature:
            return None

        raw = base64.urlsafe_b64decode(payload_b64 + "==")
        return json.loads(raw.decode())
    except Exception:
        return None
