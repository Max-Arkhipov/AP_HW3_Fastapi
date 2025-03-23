from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.auth import UserCreate, Token, UserLogin
from src.services.auth_service import create_user, authenticate_user, create_access_token
from src.database import get_async_session
from datetime import timedelta

router = APIRouter()

@router.post("/register", response_model=Token)
async def register(
    user: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    new_user = await create_user(db, user)
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": new_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_session)
):
    user = await authenticate_user(db, UserLogin(username=form_data.username, password=form_data.password))
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}