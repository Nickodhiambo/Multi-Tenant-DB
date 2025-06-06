import pytest
from httpx import AsyncClient
from app.models.core import CoreUser
from app.models.tenant import TenantUser
from app.core.security import get_password_hash

class TestAuth:
    
    @pytest.mark.asyncio
    async def test_core_user_registration(self, client: AsyncClient):
        """Test core user registration"""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_core_user_registration_duplicate_email(self, client: AsyncClient, test_core_db):
        """Test core user registration with duplicate email"""
        # Create user first
        existing_user = CoreUser(
            email="existing@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Existing User"
        )
        test_core_db.add(existing_user)
        await test_core_db.commit()
        
        # Try to register with same email
        user_data = {
            "email": "existing@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
        
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_tenant_user_registration(self, client: AsyncClient):
        """Test tenant user registration"""
        user_data = {
            "email": "tenant@example.com",
            "password": "testpassword123",
            "full_name": "Tenant User"
        }
        
        headers = {"X-TENANT": "testorg"}
        response = await client.post("/api/auth/register", json=user_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
    
    @pytest.mark.asyncio
    async def test_core_user_login(self, client: AsyncClient, test_core_db):
        """Test core user login"""
        # Create user first
        user = CoreUser(
            email="login@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Login User"
        )
        test_core_db.add(user)
        await test_core_db.commit()
        
        # Login
        login_data = {
            "email": "login@example.com",
            "password": "password123"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_core_user_login_invalid_credentials(self, client: AsyncClient):
        """Test core user login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_tenant_user_login(self, client: AsyncClient, test_tenant_db):
        """Test tenant user login"""
        # Create tenant user first
        user = TenantUser(
            email="tenant@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Tenant User"
        )
        test_tenant_db.add(user)
        await test_tenant_db.commit()
        
        # Login
        login_data = {
            "email": "tenant@example.com",
            "password": "password123"
        }
        
        headers = {"X-TENANT": "testorg"}
        response = await client.post("/api/auth/login", json=login_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"