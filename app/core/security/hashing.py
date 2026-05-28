from passlib.context import CryptContext

#passlib[bcrypt] - nao funciona bem no windows + python 3.13
#passlib[argon2]

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

class Hash:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
