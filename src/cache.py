import redis.asyncio as redis
import json
from contextlib import asynccontextmanager

REDIS_URL = "redis://localhost:6379/0"
redis_client = None

@asynccontextmanager
async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL)
    try:
        yield redis_client
    finally:
        pass

async def cache_set(key: str, value: any, ttl: int = 3600):
    async with get_redis() as client:
        await client.setex(key, ttl, json.dumps(value))

async def cache_get(key: str) -> any:
    async with get_redis() as client:
        value = await client.get(key)
        return json.loads(value) if value else None

async def cache_delete(key: str):
    async with get_redis() as client:
        await client.delete(key)