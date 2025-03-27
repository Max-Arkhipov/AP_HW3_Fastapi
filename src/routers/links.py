import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.link import LinkCreate, LinkUpdate, Link
from src.services.link_service import create_link, get_link, update_link, delete_link, get_link_stats, \
    search_link_by_url, get_expired_links, get_links_project
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

@router.get("/get_link/{short_code}", response_model=Link)
async def read_link(short_code: str, db: AsyncSession = Depends(get_async_session)):
    link = await get_link(db, short_code)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found or expired")
    return link

@router.put("/put_link/{short_code}", response_model=Link)
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

@router.delete("/delete_link/{short_code}")
async def delete_link_endpoint(
    short_code: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    success = await delete_link(db, short_code, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Link not found or unauthorized")
    return {"message": "Link deleted"}

@router.get("/stats/{short_code}")
async def read_link_stats(short_code: str, db: AsyncSession = Depends(get_async_session)):
    stats = await get_link_stats(db, short_code)
    if stats is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return stats

@router.get("/search", response_model=Link)
async def search_link(
    original_url: str = Query(..., description="The original URL to search for"),
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    link = await search_link_by_url(db, original_url, current_user)
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found, expired, or unauthorized")
    return link

@router.get("/expired", response_model=list[Link])
async def get_expired_links_history(
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    links = await get_expired_links(db, current_user)
    return links

@router.get("/project/{project}", response_model=list[Link])
async def get_links_by_project(
    project: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)
):
    links = await get_links_project(db, project, current_user)
    return links