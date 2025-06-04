from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.security import verify_token
from app.database.core import db_manager
from app.schemas.auth import TokenData
from app.models.core import CoreUser
from app.models.tenant import TenantUser
from sqlalchemy import select

security = HTTPBearer()

async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data

async def get_core_db() -> AsyncSession:
    session = await db_manager.get_core_session()
    try:
        yield session
    finally:
        await session.close()

async def get_tenant_db(request: Request) -> AsyncSession:
    tenant_slug = request.headers.get("X-TENANT")
    if not tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-TENANT header is required"
        )
    
    session = await db_manager.get_tenant_session(tenant_slug)
    try:
        yield session
    finally:
        await session.close()

async def get_current_core_user(
    token_data: TokenData = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_core_db)
) -> CoreUser:
    if token_data.context != "core":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Core authentication required"
        )
    
    result = await db.execute(select(CoreUser).where(CoreUser.id == token_data.user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

async def get_current_tenant_user(
    request: Request,
    token_data: TokenData = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_tenant_db)
) -> TenantUser:
    tenant_slug = request.headers.get("X-TENANT")
    
    if token_data.context != "tenant" or token_data.tenant != tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant authentication required for this tenant"
        )
    
    result = await db.execute(select(TenantUser).where(TenantUser.id == token_data.user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

def get_tenant_slug(request: Request) -> Optional[str]:
    return request.headers.get("X-TENANT")