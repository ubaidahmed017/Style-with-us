"""Shared pytest fixtures.

Most of the suite is infra-free (Pydantic validators, pure functions, RBAC with a
fake session). DB-backed integration tests are gated behind a real Postgres URL
because the schema uses Postgres-only column types (UUID, ENUM), so SQLite can't
stand in. Set STYLEWITHUS_TEST_DATABASE_URL to an async Postgres DSN to run them,
e.g. postgresql+asyncpg://user:pass@localhost:5432/stylewithus_test
"""

import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from app.main import app
from app.core.database import get_db
from app.models.base import Base

TEST_DB_URL = os.getenv("STYLEWITHUS_TEST_DATABASE_URL")

# Decorator for tests that need a real Postgres.
requires_db = pytest.mark.skipif(
    TEST_DB_URL is None,
    reason="set STYLEWITHUS_TEST_DATABASE_URL (async Postgres DSN) to run DB tests",
)


@pytest_asyncio.fixture
async def test_db():
    """A clean schema + session bound to the app via dependency override."""
    if not TEST_DB_URL:
        pytest.skip("no test database configured")

    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        async def _override_get_db():
            yield session

        app.dependency_overrides[get_db] = _override_get_db
        yield session
        app.dependency_overrides.pop(get_db, None)

    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db):
    """HTTP client wired to the ASGI app with the test DB override in place."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_firebase_token():
    return {
        "uid": "test-user-123",
        "email": "test@example.com",
        "email_verified": True,
    }
