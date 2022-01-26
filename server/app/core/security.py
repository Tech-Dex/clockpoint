from bcrypt import gensalt
from passlib.context import CryptContext

crypt_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_salt() -> str:
    return gensalt().decode()


def hash_password(salt: str, password: str) -> str:
    return crypt_context.hash(salt + password)


def verify_password(salt: str, password: str, hashed_password: str) -> bool:
    return crypt_context.verify(salt + password, hashed_password)
