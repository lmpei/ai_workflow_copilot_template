import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).with_name("test_app.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.resolve().as_posix()}"

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.core.database import reset_database_for_tests  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    reset_database_for_tests()
    with TestClient(app) as test_client:
        yield test_client
