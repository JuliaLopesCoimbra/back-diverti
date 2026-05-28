from pydantic import BaseModel

class VerifyEmailRequest(BaseModel):
    token: str
