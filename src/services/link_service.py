import logging
from urllib.parse import unquote
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from src.models import Link
from src.schemas.link import LinkCreate, LinkUpdate, LinkSchema
from src.utils import generate_short_code
from src.cache import cache_set, cache_get, cache_delete

async def create_link(db: AsyncSession, link: LinkCreate, current_user: dict | None):
    existing_link_query = select(Link).filter(
        Link.original_url == link.original_url,
        Link.user_id == (current_user["id"] if current_user else None),
        Link.is_active == True
    ).filter(
        (Link.expires_at.is_(None)) | (Link.expires_at > datetime.now(timezone.utc))
    )
    result = await db.execute(existing_link_query)
    existing_link = result.scalar_one_or_none()

    if existing_link:
        return existing_link

    short_code = link.short_code or generate_short_code()
    while (await db.execute(select(Link).filter(Link.short_code == short_code))).scalar():
        short_code = generate_short_code()
    new_link = Link(
        original_url=link.original_url,
        short_code=short_code,
        created_at=datetime.utcnow(),
        user_id=current_user.get("id") if current_user else None,
        expires_at=link.expires_at,
        clicks=0,
        last_used=None,
        project=link.project,
    )
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)

    link_data = LinkSchema.model_validate(new_link).model_dump(by_alias=True, mode="json")
    await cache_set(f"link:{new_link.short_code}", link_data)
    await cache_set(f"search:{new_link.original_url}:{current_user['id'] if current_user else 'anon'}", link_data)

    return new_link

async def get_link(db: AsyncSession, short_code: str):
    cache_key = f"link:{short_code}"
    cached = await cache_get(cache_key)
    if cached:
        link = LinkSchema.model_validate(cached)
        if link.is_active and (not link.expires_at or link.expires_at > datetime.now(timezone.utc)):
            link.clicks += 1
            link.last_used = datetime.utcnow()
            await cache_set(cache_key, link.model_dump(by_alias=True, mode="json"))
            return link
        else:
            await cache_delete(cache_key)
            return None

    result = await db.execute(select(Link).filter(Link.short_code == short_code, Link.is_active == True))
    link = result.scalar_one_or_none()
    if link and (not link.expires_at or link.expires_at > datetime.now(timezone.utc)):
        link.clicks += 1
        link.last_used = datetime.utcnow()
        await db.commit()
        link_data = LinkSchema.model_validate(link).model_dump(by_alias=True, mode="json")
        await cache_set(cache_key, link_data)
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

    link_data_cache = LinkSchema.model_validate(link).model_dump(by_alias=True, mode="json")
    await cache_set(f"link:{short_code}", link_data_cache)
    await cache_delete(f"link_stats:{short_code}")
    await cache_set(f"search:{link.original_url}:{current_user['id']}", link_data_cache)

    return link

async def delete_link(db: AsyncSession, short_code: str, current_user: dict):
    result = await db.execute(select(Link).filter(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if not link or (link.user_id != current_user.get("id")):
        return False
    await db.delete(link)
    await db.commit()

    await cache_delete(f"link:{short_code}")
    await cache_delete(f"link_stats:{short_code}")
    await cache_delete(f"search:{link.original_url}:{current_user['id'] if current_user else 'anon'}")

    return True

async def get_link_stats(db: AsyncSession, short_code: str):
    cache_key = f"link_stats:{short_code}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    result = await db.execute(select(Link).filter(Link.short_code == short_code))
    link = result.scalar_one_or_none()
    if not link:
        return None

    stats = {
        "original_url": link.original_url,
        "created_at": link.created_at.isoformat(),
        "clicks": link.clicks,
        "last_used": link.last_used.isoformat() if link.last_used else None
    }
    await cache_set(cache_key, stats, ttl=300)
    return stats

async def search_link_by_url(db: AsyncSession, original_url: str, current_user: dict | None):
    cache_key = f"search:{original_url}:{current_user['id'] if current_user else 'anon'}"
    cached = await cache_get(cache_key)
    if cached:
        return LinkSchema.model_validate(cached) if cached else None

    result = await db.execute(select(Link).filter(Link.original_url == original_url, Link.is_active == True))
    link = result.scalar_one_or_none()
    if not link:
        await cache_set(cache_key, None, ttl=600)
        return None
    if current_user and link.user_id != current_user.get("id"):
        return None
    if link.expires_at and link.expires_at <= datetime.now(timezone.utc):
        return None
    link_data = LinkSchema.model_validate(link).model_dump(by_alias=True, mode="json")
    await cache_set(cache_key, link_data, ttl=600)
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
    query = select(Link).filter(Link.project == project)
    if current_user:
        query = query.filter(Link.user_id == current_user.get("id"))
    result = await db.execute(query)
    links = result.scalars().all()
    return links