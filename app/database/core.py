from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import Dict, Optional
import asyncpg
from app.config import settings

class Base(DeclarativeBase):
    pass

class DatabaseManager:
    def __init__(self):
        self._engines: Dict[str, any] = {}
        self._sessions: Dict[str, any] = {}
        
    async def get_core_engine(self):
        if "core" not in self._engines:
            self._engines["core"] = create_async_engine(
                settings.database_url,
                echo=True,
                pool_pre_ping=True
            )
        return self._engines["core"]
    
    async def get_tenant_engine(self, tenant_slug: str):
        if tenant_slug not in self._engines:
            # Construct tenant database URL
            base_url = settings.database_url.rsplit('/', 1)[0]
            tenant_db_url = f"{base_url}/multitenant_{tenant_slug}"
            
            self._engines[tenant_slug] = create_async_engine(
                tenant_db_url,
                echo=True,
                pool_pre_ping=True
            )
        return self._engines[tenant_slug]
    
    async def get_core_session(self) -> AsyncSession:
        engine = await self.get_core_engine()
        if "core" not in self._sessions:
            self._sessions["core"] = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
        return self._sessions["core"]()
    
    async def get_tenant_session(self, tenant_slug: str) -> AsyncSession:
        engine = await self.get_tenant_engine(tenant_slug)
        if tenant_slug not in self._sessions:
            self._sessions[tenant_slug] = async_sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
        return self._sessions[tenant_slug]()
    
    async def create_tenant_database(self, tenant_slug: str):
        """Create a new database for a tenant"""
        # Connect to PostgreSQL without specifying a database
        base_url = settings.database_url.replace('+asyncpg', '').rsplit('/', 1)[0]
        
        # Extract connection components
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database='postgres'  # Connect to default postgres database
        )
        
        try:
            # Create the tenant database
            db_name = f"multitenant_{tenant_slug}"
            await conn.execute(f'CREATE DATABASE "{db_name}"')
        except asyncpg.DuplicateDatabaseError:
            # Database already exists
            pass
        finally:
            await conn.close()
    
    async def create_tenant_tables(self, tenant_slug: str):
        """Create tables in tenant database"""
        from app.models.tenant import TenantBase
        engine = await self.get_tenant_engine(tenant_slug)
        async with engine.begin() as conn:
            await conn.run_sync(TenantBase.metadata.create_all)

db_manager = DatabaseManager()