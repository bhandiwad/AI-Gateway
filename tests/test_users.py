"""
User management tests for AI Gateway.
Tests for user CRUD operations within a tenant.
"""
import pytest
from httpx import AsyncClient


class TestUserCreation:
    """Tests for creating users within a tenant."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient, auth_headers: dict):
        """Test creating a new user in the tenant."""
        response = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "newuser@tenant.com",
                "name": "New User",
                "role": "user"
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["email"] == "newuser@tenant.com"
    
    @pytest.mark.asyncio
    async def test_create_user_with_admin_role(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Test creating a user with admin role."""
        response = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "admin@tenant.com",
                "name": "Admin User",
                "role": "admin"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_create_duplicate_user_fails(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that creating duplicate user fails."""
        user_data = {
            "email": "duplicate@tenant.com",
            "name": "Duplicate User",
            "role": "user"
        }
        
        await client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=auth_headers
        )
        
        response = await client.post(
            "/api/v1/admin/users",
            json=user_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400


class TestUserListing:
    """Tests for listing users."""
    
    @pytest.mark.asyncio
    async def test_list_users(self, client: AsyncClient, auth_headers: dict):
        """Test listing users in tenant."""
        response = await client.get(
            "/api/v1/admin/users",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "users" in data
    
    @pytest.mark.asyncio
    async def test_list_users_without_auth_fails(self, client: AsyncClient):
        """Test that listing users without auth fails."""
        response = await client.get("/api/v1/admin/users")
        
        assert response.status_code in [401, 403]


class TestUserRetrieval:
    """Tests for retrieving individual users."""
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client: AsyncClient, auth_headers: dict):
        """Test getting a user by ID."""
        create_response = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "getuser@tenant.com",
                "name": "Get User",
                "role": "user"
            },
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            user_id = create_response.json()["id"]
            
            response = await client.get(
                f"/api/v1/admin/users/{user_id}",
                headers=auth_headers
            )
            
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent user."""
        response = await client.get(
            "/api/v1/admin/users/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestUserUpdate:
    """Tests for updating users."""
    
    @pytest.mark.asyncio
    async def test_update_user_name(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test updating user name."""
        create_response = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "updatename@tenant.com",
                "name": "Original Name",
                "role": "user"
            },
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            user_id = create_response.json()["id"]
            
            response = await client.patch(
                f"/api/v1/admin/users/{user_id}",
                json={"name": "Updated Name"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.json()["name"] == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_update_user_role(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Test updating user role."""
        create_response = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "updaterole@tenant.com",
                "name": "Role User",
                "role": "user"
            },
            headers=admin_auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            user_id = create_response.json()["id"]
            
            response = await client.patch(
                f"/api/v1/admin/users/{user_id}",
                json={"role": "admin"},
                headers=admin_auth_headers
            )
            
            assert response.status_code == 200


class TestUserDeletion:
    """Tests for deleting users."""
    
    @pytest.mark.asyncio
    async def test_delete_user(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a user."""
        create_response = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "deleteuser@tenant.com",
                "name": "Delete User",
                "role": "user"
            },
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            user_id = create_response.json()["id"]
            
            response = await client.delete(
                f"/api/v1/admin/users/{user_id}",
                headers=auth_headers
            )
            
            assert response.status_code in [200, 204]
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent user."""
        response = await client.delete(
            "/api/v1/admin/users/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestUserPermissions:
    """Tests for user permission management."""
    
    @pytest.mark.asyncio
    async def test_user_roles_endpoint(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting available user roles."""
        response = await client.get(
            "/api/v1/admin/users/roles",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestUserUsage:
    """Tests for user usage tracking."""
    
    @pytest.mark.asyncio
    async def test_get_user_usage(self, client: AsyncClient, auth_headers: dict):
        """Test getting user usage statistics."""
        create_response = await client.post(
            "/api/v1/admin/users",
            json={
                "email": "usageuser@tenant.com",
                "name": "Usage User",
                "role": "user"
            },
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            user_id = create_response.json()["id"]
            
            response = await client.get(
                f"/api/v1/admin/users/{user_id}/usage",
                headers=auth_headers
            )
            
            assert response.status_code == 200
