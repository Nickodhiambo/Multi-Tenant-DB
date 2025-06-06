import pytest
from httpx import AsyncClient
from app.models.core import CoreUser
from app.core.security import get_password_hash, create_access_token

class TestOrganizations:
    
    @pytest.mark.asyncio
    async def test_create_organization_success(self, client: AsyncClient, test_core_db):
        """Test successful organization creation"""
        # Create and authenticate a user
        user = CoreUser(
            email="owner@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Organization Owner"
        )
        test_core_db.add(user)
        await test_core_db.commit()
        await test_core_db.refresh(user)
        
        # Create access token
        access_token = create_access_token(data={"user_id": user.id, "context": "core"})
        
        # Create organization
        org_data = {
            "name": "Test Organization",
            "slug": "test-org",
            "description": "A test organization"
        }
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.post("/api/organizations/", json=org_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == org_data["name"]
        assert data["slug"] == org_data["slug"]
        assert data["owner_id"] == user.id
    
    @pytest.mark.asyncio
    async def test_create_organization_unauthenticated(self, client: AsyncClient):
        """Test organization creation without authentication"""
        org_data = {
            "name": "Test Organization",
            "slug": "test-org",
            "description": "A test organization"
        }
        
        response = await client.post("/api/organizations/", json=org_data)
        
        assert response.status_code == 403  # Forbidden due to missing auth
    
    @pytest.mark.asyncio
    async def test_create_organization_invalid_slug(self, client: AsyncClient, test_core_db):
        """Test organization creation with invalid slug"""
        # Create and authenticate a user
        user = CoreUser(
            email="owner2@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Organization Owner"
        )
        test_core_db.add(user)
        await test_core_db.commit()
        await test_core_db.refresh(user)
        
        # Create access token
        access_token = create_access_token(data={"user_id": user.id, "context": "core"})
        
        # Try to create organization with invalid slug
        org_data = {
            "name": "Test Organization",
            "slug": "INVALID-SLUG!",  # Invalid characters
            "description": "A test organization"
        }
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.post("/api/organizations/", json=org_data, headers=headers)
        
        assert response.status_code == 400
        assert "Invalid slug format" in response.json()["detail"]