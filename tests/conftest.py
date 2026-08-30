from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.database import db
from app.main import app


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None]:
    """Ensure in-memory database has clean, seeded state for each test."""
    db.clear()
    db.seed(count=2500)
    yield
    db.clear()


@pytest.fixture
def client() -> Generator[TestClient, None]:
    """Provide a TestClient instance for API requests."""
    with TestClient(app) as test_client:
        yield test_client
