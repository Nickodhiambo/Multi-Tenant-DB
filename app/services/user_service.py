from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import CoreUser
from app.models.tenant import TenantUser
from app.schemas.auth import UserRegister
from app.core.security import get_password_hash, verify_password
from typing import Optional

class UserService:
    @staticmethod
    async def create_core_user(db: AsyncSession, user_data: UserRegister) -> CoreUser:
        # Check if user already exists
        result = await db.execute(select(CoreUser).where(CoreUser.email == user_data.email))
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")
        
        hashed_password = get_password_hash(user_data.password)
        db_user = CoreUser(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    @staticmethod
    async def create_tenant_user(db: AsyncSession, user_data: UserRegister) -> TenantUser:
        # Check if user already exists
        result = await db.execute(select(TenantUser).where(TenantUser.email == user_data.email))
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")
        
        hashed_password = get_password_hash(user_data.password)
        db_user = TenantUser(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    @staticmethod
    async def authenticate_core_user(db: AsyncSession, email: str, password: str) -> Optional[CoreUser]:
        result = await db.execute(select(CoreUser).where(CoreUser.email == email))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    @staticmethod
    async def authenticate_tenant_user(db: AsyncSession, email: str, password: str) -> Optional[TenantUser]:
        result = await db.execute(select(TenantUser).where(TenantUser.email == email))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        return user
