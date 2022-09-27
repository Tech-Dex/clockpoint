from bcrypt import gensalt
from passlib.context import CryptContext

crypt_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_salt() -> str:
    return gensalt().decode()


def hash_password(salt: str, password: str) -> str:
    return crypt_context.hash(salt + password)


def verify_password(salt: str, password: str, hashed_password: str) -> bool:
    return crypt_context.verify(salt + password, hashed_password)


def validate_password(password: str) -> list[str]:
    validations = {
        "has_min_length_8": lambda string: len(string) >= 8,
        "has_uppercase": lambda string: any(char.isupper() for char in string),
        "has_lowercase": lambda string: any(char.islower() for char in string),
        "has_number": lambda string: any(char.isdigit() for char in string),
        "has_special_char": lambda string: any(
            char for char in string if not char.isalnum() and not char.isspace()
        ),
        "has_no_whitespace": lambda string: not any(char.isspace() for char in string),
    }
    warnings: list[str] = []
    for name, validation in validations.items():
        if not validation(password):
            warnings.append(name)

    return warnings
