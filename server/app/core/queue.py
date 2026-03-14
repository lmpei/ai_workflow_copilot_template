from urllib.parse import urlparse

from arq.connections import RedisSettings

from app.core.config import get_settings


def build_redis_settings() -> RedisSettings:
    parsed = urlparse(get_settings().redis_url)
    database = parsed.path.lstrip("/")
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(database or "0"),
        password=parsed.password,
        ssl=parsed.scheme == "rediss",
    )
