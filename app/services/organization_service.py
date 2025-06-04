from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.core import Organization, CoreUser
from app.models.tenant import TenantUser
from app.schemas.organization import OrganizationCreate
from app.database.core import db_manager
from app.core.security import get_password_hash
import re

class OrganizationService:
    @staticmethod
    def validate_slug(slug: str) -> bool:
        """Validate organization slug format"""
        return bool(re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$', slug)) and len(slug) >= 2
    
    @staticmethod
    async def create_organization(
        db: AsyncSession, 
        org_data: OrganizationCreate, 
        owner: CoreUser
    ) -> Organization:
        # Validate slug
        if not OrganizationService.validate_slug(org_data.slug):
            raise ValueError("Invalid slug format")
        
        # Check if organization with slug already exists
        result = await db.execute(select(Organization).where(Organization.slug == org_data.slug))
        if result.scalar_one_or_none():
            raise ValueError("Organization slug already exists")
        
        # Create organization
        db_org = Organization(
            name=org_data.name,
            slug=org_data.slug,
            description=org_data.description,
            owner_id=owner.id
        )
        
        db.add(db_org)
        await db.commit()
        await db.refresh(db_org)
        
        # Create tenant database and tables
        await db_manager.create_tenant_database(org_data.slug)
        await db_manager.create_tenant_tables(org_data.slug)
        
        # Sync owner to tenant database
        await OrganizationService.sync_owner_to_tenant(org_data.slug, owner)
        
        return db_org
    
    @staticmethod
    async def sync_owner_to_tenant(tenant_slug: str, owner: CoreUser):
        """Sync organization owner to tenant database"""
        tenant_db = await db_manager.get_tenant_session(tenant_slug)
        
        try:
            # Check if owner already exists in tenant database
            result = await tenant_db.execute(
                select(TenantUser).where(TenantUser.email == owner.email)
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # Create owner in tenant database
                tenant_user = TenantUser(
                    email=owner.email,
                    hashed_password=owner.hashed_password,
                    full_name=owner.full_name
                )
                
                tenant_db.add(tenant_user)
                await tenant_db.commit()
        finally:
            await tenant_db.close()
