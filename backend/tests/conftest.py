import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.firebase import initialize_firebase

# Test database URL - uses in-memory SQLite for speed
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database and session"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = AsyncSession(engine, expire_on_commit=False)

    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    yield async_session

    await async_session.close()
    await engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_firebase_token():
    """Mock Firebase token for testing"""
    return {
        "uid": "test-user-123",
        "email": "test@example.com",
        "email_verified": True,
        "iat": 1234567890,
        "exp": 9999999999,
    }


@pytest.fixture
def mock_decoded_token(mock_firebase_token):
    """Create mock decoded Firebase token"""
    class MockDecodedToken:
        def __getitem__(self, key):
            return mock_firebase_token.get(key)

        def get(self, key, default=None):
            return mock_firebase_token.get(key, default)

    return MockDecodedToken()
