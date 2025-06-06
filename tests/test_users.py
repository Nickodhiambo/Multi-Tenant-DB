import pytest
from httpx import AsyncClient
from app.models.tenant import TenantUser
from app.core.security import get_password_hash, create_access_token

class TestUsers:
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self, client: AsyncClient, test_tenant_db):
        """Test getting user profile"""
        # Create tenant user
        user = TenantUser(
            email="profile@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Profile User",
            bio="Test bio",
            phone="123-456-7890"
        )
        test_tenant_db.add(user)
        await test_tenant_db.commit()
        await test_tenant_db.refresh(user)
        
        # Create access token
        access_token = create_access_token(
            data={"user_id": user.id, "context": "tenant", "tenant": "testorg"}
        )
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-TENANT": "testorg"
        }
        response = await client.get("/api/users/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert data["full_name"] == user.full_name
        assert data["bio"] == user.bio
        assert data["phone"] == user.phone
    
    @pytest.mark.asyncio
    async def test_update_user_profile(self, client: AsyncClient, test_tenant_db):
        """Test updating user profile"""
        # Create tenant user
        user = TenantUser(
            email="update@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Update User"
        )
        test_tenant_db.add(user)
        await test_tenant_db.commit()
        await test_tenant_db.refresh(user)
        
        # Create access token
        access_token = create_access_token(
            data={"user_id": user.id, "context": "tenant", "tenant": "testorg"}
        )
        
        # Update profile
        update_data = {
            "full_name": "Updated Name",
            "bio": "Updated bio",
            "phone": "987-654-3210"
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-TENANT": "testorg"
        }
        response = await client.put("/api/users/me", json=update_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["bio"] == update_data["bio"]
        assert data["phone"] == update_data["phone"]
    
    @pytest.mark.asyncio
    async def test_get_user_profile_wrong_tenant(self, client: AsyncClient, test_tenant_db):
        """Test getting user profile with wrong tenant header"""
        # Create tenant user
        user = TenantUser(
            email="wrong@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Wrong Tenant User"
        )
        test_tenant_db.add(user)
        await test_tenant_db.commit()
        await test_tenant_db.refresh(user)
        
        # Create access token for different tenant
        access_token = create_access_token(
            data={"user_id": user.id, "context": "tenant", "tenant": "othertenant"}
        )
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-TENANT": "testorg"  # Different tenant
        }
        response = await client.get("/api/users/me", headers=headers)
        
        assert response.status_code == 403  # Forbidden