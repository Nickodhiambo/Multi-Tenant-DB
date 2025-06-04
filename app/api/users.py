from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import TenantUserResponse, TenantUserUpdate
from app.core.deps import get_tenant_db, get_current_tenant_user
from app.models.tenant import TenantUser

router = APIRouter()

@router.get("/me", response_model=TenantUserResponse)
async def get_current_user_profile(
    current_user: TenantUser = Depends(get_current_tenant_user)
):
    """Get current user profile from tenant database"""
    return TenantUserResponse.model_validate(current_user)

@router.put("/me", response_model=TenantUserResponse)
async def update_current_user_profile(
    request: Request,
    user_update: TenantUserUpdate,
    current_user: TenantUser = Depends(get_current_tenant_user),
    db: AsyncSession = Depends(get_tenant_db)
):
    """Update current user profile in tenant database"""
    
    # Update user fields
    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return TenantUserResponse.model_validate(current_user)