from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(slots=True)
class DatabaseConfig:
    url: str
    driver: str


def get_database_config() -> DatabaseConfig:
    settings = get_settings()
    driver = settings.database_url.split(":", 1)[0]
    return DatabaseConfig(url=settings.database_url, driver=driver)
