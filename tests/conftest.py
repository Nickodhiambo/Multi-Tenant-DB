import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database.core import db_manager, Base
from app.models.tenant import TenantBase
from app.core.deps import get_core_db, get_tenant_db
import os

# Test database URLs
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
TEST_TENANT_DATABASE_URL = "sqlite+aiosqlite:///./test_tenant.db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_core_engine():
    """Create test core database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()
    # Clean up test database
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture
async def test_tenant_engine():
    """Create test tenant database engine."""
    engine = create_async_engine(
        TEST_TENANT_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(TenantBase.metadata.create_all)
    
    yield engine
    
    await engine.dispose()
    # Clean up test database
    if os.path.exists("./test_tenant.db"):
        os.remove("./test_tenant.db")

@pytest.fixture
async def test_core_db(test_core_engine):
    """Create test core database session."""
    async_session = async_sessionmaker(
        test_core_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest.fixture
async def test_tenant_db(test_tenant_engine):
    """Create test tenant database session."""
    async_session = async_sessionmaker(
        test_tenant_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest.fixture
async def client(test_core_db, test_tenant_db):
    """Create test client with database overrides."""
    
    async def override_get_core_db():
        yield test_core_db
    
    async def override_get_tenant_db():
        yield test_tenant_db
    
    app.dependency_overrides[get_core_db] = override_get_core_db
    app.dependency_overrides[get_tenant_db] = override_get_tenant_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac
    
    app.dependency_overrides.clear()