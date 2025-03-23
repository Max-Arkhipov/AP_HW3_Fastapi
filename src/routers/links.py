from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.link import LinkCreate, LinkUpdate, Link
from src.services.link_service import create_link, get_link, update_link, delete_link, get_link_stats
from src.services.auth_service import get_current_user
from src.database import get_async_session

router = APIRouter()

@router.post("/shorten", response_model=Link)
async def shorten_link(
    link: LinkCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    return await create_link(db, link, current_user)

@router.get("/{short_code}", response_model=Link)
async def read_link(short_code: str, db: AsyncSession = Depends(get_async_session)):
    link = await get_link(db, short_code)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found or expired")
    return link

@router.put("/{short_code}", response_model=Link)
async def update_link_endpoint(
    short_code: str,
    link: LinkUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    updated_link = await update_link(db, short_code, link, current_user)
    if updated_link is None:
        raise HTTPException(status_code=404, detail="Link not found or unauthorized")
    return updated_link

@router.delete("/{short_code}")
async def delete_link_endpoint(
    short_code: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    success = await delete_link(db, short_code, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Link not found or unauthorized")
    return {"message": "Link deleted"}

@router.get("/{short_code}/stats")
async def read_link_stats(short_code: str, db: AsyncSession = Depends(get_async_session)):
    stats = await get_link_stats(db, short_code)
    if stats is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return stats