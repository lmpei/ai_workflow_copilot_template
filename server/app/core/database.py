from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock

from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models import Base

_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None
_INITIALIZED_URLS: set[str] = set()
_LOCK = Lock()


@dataclass(slots=True)


class DatabaseConfig:
    url: str
    driver: str


def get_database_config() -> DatabaseConfig:
    settings = get_settings()
    driver = settings.database_url.split(":", 1)[0]
    return DatabaseConfig(url=settings.database_url, driver=driver)


def _build_connect_args(url: str) -> dict[str, object]:
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def get_engine() -> Engine:
    global _ENGINE

    if _ENGINE is None:
        config = get_database_config()
        _ENGINE = create_engine(
            config.url,
            connect_args=_build_connect_args(config.url),
            future=True,
        )
    return _ENGINE


def get_session_factory() -> sessionmaker[Session]:
    global _SESSION_FACTORY

    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _SESSION_FACTORY


def _validate_database_schema() -> None:
    inspector = inspect(get_engine())
    expected_tables = set(Base.metadata.tables)
    existing_tables = set(inspector.get_table_names())
    missing_tables = sorted(expected_tables - existing_tables)
    if missing_tables:
        raise RuntimeError(
            "Database schema is missing tables after initialization: "
            f"{', '.join(missing_tables)}. Run `alembic upgrade head` before starting the app."
        )

    missing_columns_by_table: list[str] = []
    for table_name, table in Base.metadata.tables.items():
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        missing_columns = sorted(set(table.columns.keys()) - existing_columns)
        if missing_columns:
            missing_columns_by_table.append(
                f"{table_name} ({', '.join(missing_columns)})"
            )

    if missing_columns_by_table:
        raise RuntimeError(
            "Database schema is out of date; run `alembic upgrade head` before starting the app. "
            "Missing columns: "
            f"{'; '.join(missing_columns_by_table)}"
        )


def ensure_database_ready() -> None:
    url = get_database_config().url
    if url in _INITIALIZED_URLS:
        return

    with _LOCK:
        if url in _INITIALIZED_URLS:
            return
        Base.metadata.create_all(bind=get_engine())
        _validate_database_schema()
        _INITIALIZED_URLS.add(url)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    ensure_database_ready()
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    ensure_database_ready()
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def reset_database_for_tests() -> None:
    global _ENGINE
    global _SESSION_FACTORY

    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _INITIALIZED_URLS.discard(get_database_config().url)
    engine.dispose()
    _ENGINE = None
    _SESSION_FACTORY = None
