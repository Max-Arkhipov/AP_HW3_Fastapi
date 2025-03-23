from passlib.context import CryptContext

import random
import string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def generate_short_code(length: int = 6) -> str:
    """Генерирует уникальный короткий код."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))