from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models import Link
from src.schemas.link import LinkCreate, LinkUpdate
from src.utils import generate_short_code
from datetime import datetime

async def create_link(db: AsyncSession, link: LinkCreate, current_user: dict | None):
    short_code = link.custom_alias or generate_short_code()
    while (await db.execute(select(Link).filter(Link.short_code == short_code))).scalar():
        short_code = generate_short_code()
    new_link = Link(
        original_url=link.original_url,
        short_code=short_code,
        user_id=current_user.get("id") if current_user else None,
        expires_at=link.expires_at
    )
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)
    return new_link

async def get_link(db: AsyncSession, short_code: str):
    result = await db.execute(select(Link).filter(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if link and (not link.expires_at or link.expires_at > datetime.utcnow()):
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