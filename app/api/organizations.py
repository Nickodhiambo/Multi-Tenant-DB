from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from app.services.organization_service import OrganizationService
from app.core.deps import get_core_db, get_current_core_user
from app.models.core import CoreUser

router = APIRouter()

@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: CoreUser = Depends(get_current_core_user),
    db: AsyncSession = Depends(get_core_db)
):
    """Create a new organization (requires core authentication)"""
    try:
        organization = await OrganizationService.create_organization(
            db, org_data, current_user
        )
        return OrganizationResponse.model_validate(organization)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )