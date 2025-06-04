from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.auth import UserRegister, UserLogin, UserResponse, TenantUserResponse, Token
from app.services.user_service import UserService
from app.core.deps import get_core_db, get_tenant_db, get_tenant_slug
from app.core.security import create_access_token

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse)
async def register(
    request: Request,
    user_data: UserRegister,
    tenant_slug: str = Depends(get_tenant_slug),
    core_db: AsyncSession = Depends(get_core_db)
):
    """Register user - routes to core or tenant based on X-TENANT header"""
    
    if not tenant_slug:
        # Core registration
        try:
            user = await UserService.create_core_user(core_db, user_data)
            return UserResponse.model_validate(user)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    else:
        # Tenant registration
        tenant_db = await get_tenant_db(request).__anext__()
        try:
            user = await UserService.create_tenant_user(tenant_db, user_data)
            return TenantUserResponse.model_validate(user)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        finally:
            await tenant_db.close()

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    login_data: UserLogin,
    tenant_slug: str = Depends(get_tenant_slug),
    core_db: AsyncSession = Depends(get_core_db)
):
    """Login user - routes to core or tenant based on X-TENANT header"""
    
    if not tenant_slug:
        # Core login
        user = await UserService.authenticate_core_user(
            core_db, login_data.email, login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        access_token = create_access_token(
            data={"user_id": user.id, "context": "core"}
        )
        
        return Token(access_token=access_token, token_type="bearer")
    else:
        # Tenant login
        tenant_db = await get_tenant_db(request).__anext__()
        try:
            user = await UserService.authenticate_tenant_user(
                tenant_db, login_data.email, login_data.password
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            access_token = create_access_token(
                data={"user_id": user.id, "context": "tenant", "tenant": tenant_slug}
            )
            
            return Token(access_token=access_token, token_type="bearer")
        finally:
            await tenant_db.close()