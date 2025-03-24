import logging
from urllib.parse import unquote

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models import Link
from src.schemas.link import LinkCreate, LinkUpdate
from src.utils import generate_short_code

from datetime import datetime, timezone, timedelta


async def create_link(db: AsyncSession, link: LinkCreate, current_user: dict | None):
    short_code = link.short_code or generate_short_code()
    while (await db.execute(select(Link).filter(Link.short_code == short_code))).scalar():
        short_code = generate_short_code()
    new_link = Link(
        original_url=link.original_url,
        short_code=short_code,
        created_at=datetime.utcnow(),  # Явно задаём created_at
        user_id=current_user.get("id") if current_user else None,
        expires_at=link.expires_at,
        clicks=0,  # Явно задаём начальное значение
        last_used=None,  # Указываем None явно для совместимости
        project = link.project,
    )
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return new_link

async def get_link(db: AsyncSession, short_code: str):
    result = await db.execute(select(Link).filter(Link.short_code == short_code, Link.is_active == True))
    link = result.scalar_one_or_none()
    if link and (not link.expires_at or link.expires_at > datetime.now(timezone.utc)):
        link.clicks += 1
        link.last_used = datetime.utcnow()
        await db.commit()
        return link
    return None

async def update_link(db: AsyncSession, short_code: str, link_data: LinkUpdate, current_user: dict):
    result = await db.execute(select(Link).filter(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if not link or (link.user_id != current_user.get("id")):
        return None
    if link_data.original_url:
        link.original_url = link_data.original_url
    if link_data.expires_at:
        link.expires_at = link_data.expires_at
    await db.commit()
    return link

async def delete_link(db: AsyncSession, short_code: str, current_user: dict):
    result = await db.execute(select(Link).filter(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if not link or (link.user_id != current_user.get("id")):
        return False
    await db.delete(link)
    await db.commit()
    return True

async def get_link_stats(db: AsyncSession, short_code: str):
    result = await db.execute(select(Link).filter(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if not link:
        return None
    return {
        "original_url": link.original_url,
        "created_at": link.created_at,
        "clicks": link.clicks,
        "last_used": link.last_used
    }

async def search_link_by_url(db: AsyncSession, original_url: str, current_user: dict | None):
    # decoded_url = unquote(original_url)
    result = await db.execute(select(Link).filter(Link.original_url == original_url, Link.is_active == True))
    link = result.scalar_one_or_none()
    if not link:
        return None
    if current_user and link.user_id != current_user.get("id"):
        return None
    if link.expires_at and link.expires_at <= datetime.now(timezone.utc):
        return None
    return link

async def get_expired_links(db: AsyncSession, current_user: dict | None):
    now = datetime.now(timezone.utc)
    query = select(Link).filter(Link.expires_at <= now)
    if current_user:
        query = query.filter(Link.user_id == current_user.get("id"))
    result = await db.execute(query)
    links = result.scalars().all()
    return links

async def get_links_project(db: AsyncSession, project: str, current_user: dict | None):
    query = select(Link).filter(Link.project == project, Link.is_active == True)
    if current_user:
        query = query.filter(Link.user_id == current_user.get("id"))
    result = await db.execute(query)
    links = result.scalars().all()
    return links