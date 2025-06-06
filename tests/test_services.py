import pytest
from app.services.user_service import UserService
from app.services.organization_service import OrganizationService
from app.schemas.auth import UserRegister
from app.schemas.organization import OrganizationCreate
from app.models.core import CoreUser
from app.core.security import get_password_hash

class TestUserService:
    
    @pytest.mark.asyncio
    async def test_create_core_user(self, test_core_db):
        """Test creating a core user"""
        user_data = UserRegister(
            email="service@example.com",
            password="password123",
            full_name="Service User"
        )
        
        user = await UserService.create_core_user(test_core_db, user_data)
        
        assert user.email == user_data.email
        assert user.full_name == user_data.full_name
        assert user.id is not None
    
    @pytest.mark.asyncio
    async def test_authenticate_core_user(self, test_core_db):
        """Test authenticating a core user"""
        # Create user first
        user = CoreUser(
            email="auth@example.com",
            hashed_password=get_password_hash("password123"),
            full_name="Auth User"
        )
        test_core_db.add(user)
        await test_core_db.commit()
        
        # Test authentication
        authenticated_user = await UserService.authenticate_core_user(
            test_core_db, "auth@example.com", "password123"
        )
        
        assert authenticated_user is not None
        assert authenticated_user.email == "auth@example.com"
        
        # Test wrong password
        wrong_auth = await UserService.authenticate_core_user(
            test_core_db, "auth@example.com", "wrongpassword"
        )
        
        assert wrong_auth is None

class TestOrganizationService:
    
    def test_validate_slug(self):
        """Test slug validation"""
        # Valid slugs
        assert OrganizationService.validate_slug("test-org")
        assert OrganizationService.validate_slug("my-company")
        assert OrganizationService.validate_slug("org123")
        
        # Invalid slugs
        assert not OrganizationService.validate_slug("Test-Org")  # Uppercase
        assert not OrganizationService.validate_slug("test_org")  # Underscore
        assert not OrganizationService.validate_slug("-test")     # Starts with dash
        assert not OrganizationService.validate_slug("test-")     # Ends with dash
        assert not OrganizationService.validate_slug("t")         # Too short