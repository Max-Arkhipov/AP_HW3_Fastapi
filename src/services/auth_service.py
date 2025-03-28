from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from fastapi import Security

from src.database import get_async_session
from src.models import User
from src.schemas.auth import UserCreate, UserLogin
from src.utils import hash_password, verify_password
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def create_user(db: AsyncSession, user: UserCreate):
    result = await db.execute(select(User).filter(User.username == user.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(db: AsyncSession, user: UserLogin):
    result = await db.execute(select(User).filter(User.username == user.username))
    db_user = result.scalar_one_or_none()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return db_user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class JWTError:
    pass


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.execute(select(User).filter(User.username == username))
        user = user.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return {"id": user.id, "username": user.username}  # Убедитесь, что id возвращается
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def optional_get_current_user(
        token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)),
        # Теперь auto_error работает
        db: AsyncSession = Depends(get_async_session)
):
    if not token:
        return None  # Позволяет анонимным пользователям

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None

        result = await db.execute(select(User).filter(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            return None

        return {"id": user.id, "username": user.username}
    except jwt.PyJWTError:
        return None