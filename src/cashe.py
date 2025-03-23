import redis
from src.models import Link

redis_client = redis.Redis(host="redis", port=6379, db=0)

def cache_link(short_code: str, link: Link):
    redis_client.setex(short_code, 3600, link.original_url)  # Кэш на 1 час

def get_cached_link(short_code: str):
    url = redis_client.get(short_code)
    return {"original_url": url.decode("utf-8")} if url else None

def clear_cache(short_code: str):
    redis_client.delete(short_code)