"""
Authentication tests for AI Gateway.
Tests for user registration, login, SSO, and token validation.
"""
import pytest
from httpx import AsyncClient


class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    @pytest.mark.asyncio
    async def test_register_new_user_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/admin/auth/register",
            json={
                "name": "New User",
                "email": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["tenant"]["email"] == "newuser@example.com"
        assert data["tenant"]["name"] == "New User"
        assert data["tenant"]["is_active"] is True
        assert data["tenant"]["is_admin"] is False
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email_fails(self, client: AsyncClient):
        """Test registration with duplicate email fails."""
        user_data = {
            "name": "First User",
            "email": "duplicate@example.com",
            "password": "SecurePass123!"
        }
        
        response1 = await client.post("/api/v1/admin/auth/register", json=user_data)
        assert response1.status_code == 200
        
        response2 = await client.post("/api/v1/admin/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_invalid_email_fails(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/v1/admin/auth/register",
            json={
                "name": "Test User",
                "email": "not-an-email",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_missing_fields_fails(self, client: AsyncClient):
        """Test registration with missing required fields fails."""
        response = await client.post(
            "/api/v1/admin/auth/register",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_register_returns_valid_jwt(self, client: AsyncClient):
        """Test that registration returns a valid JWT token."""
        response = await client.post(
            "/api/v1/admin/auth/register",
            json={
                "name": "JWT Test User",
                "email": "jwttest@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        me_response = await client.get(
            "/api/v1/admin/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "jwttest@example.com"


class TestUserLogin:
    """Tests for user login endpoint."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        await client.post(
            "/api/v1/admin/auth/register",
            json={
                "name": "Login Test User",
                "email": "logintest@example.com",
                "password": "SecurePass123!"
            }
        )
        
        response = await client.post(
            "/api/v1/admin/auth/login",
            json={
                "email": "logintest@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["tenant"]["email"] == "logintest@example.com"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password_fails(self, client: AsyncClient):
        """Test login with wrong password fails."""
        await client.post(
            "/api/v1/admin/auth/register",
            json={
                "name": "Wrong Pass User",
                "email": "wrongpass@example.com",
                "password": "CorrectPass123!"
            }
        )
        
        response = await client.post(
            "/api/v1/admin/auth/login",
            json={
                "email": "wrongpass@example.com",
                "password": "WrongPass123!"
            }
        )
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user_fails(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post(
            "/api/v1/admin/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePass123!"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_missing_password_fails(self, client: AsyncClient):
        """Test login without password fails."""
        response = await client.post(
            "/api/v1/admin/auth/login",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 422


class TestCurrentUser:
    """Tests for current user (me) endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting current user with valid token."""
        response = await client.get(
            "/api/v1/admin/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "name" in data
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_token_fails(self, client: AsyncClient):
        """Test getting current user without token fails."""
        response = await client.get("/api/v1/admin/auth/me")
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_fails(self, client: AsyncClient):
        """Test getting current user with invalid token fails."""
        response = await client.get(
            "/api/v1/admin/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code in [401, 403]


class TestSSO:
    """Tests for SSO endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_sso_providers(self, client: AsyncClient):
        """Test listing SSO providers."""
        response = await client.get("/api/v1/admin/auth/sso/providers")
        
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert isinstance(data["providers"], list)
    
    @pytest.mark.asyncio
    async def test_sso_discover_google(self, client: AsyncClient, auth_headers: dict):
        """Test OIDC discovery with Google."""
        response = await client.post(
            "/api/v1/admin/sso/discover",
            json={"issuer_url": "https://accounts.google.com"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "authorization_endpoint" in data
        assert "token_endpoint" in data
        assert "userinfo_endpoint" in data
    
    @pytest.mark.asyncio
    async def test_sso_initiate_nonexistent_provider_fails(
        self, client: AsyncClient
    ):
        """Test SSO initiation with non-existent provider fails."""
        response = await client.post(
            "/api/v1/admin/auth/sso/initiate",
            json={
                "provider_name": "nonexistent-provider",
                "redirect_uri": "http://localhost:3000/callback"
            }
        )
        
        assert response.status_code == 404


class TestTokenValidation:
    """Tests for token validation and expiration."""
    
    @pytest.mark.asyncio
    async def test_expired_token_rejected(self, client: AsyncClient):
        """Test that expired tokens are rejected."""
        from backend.app.core.security import create_access_token
        from datetime import timedelta
        
        expired_token = create_access_token(
            data={"sub": "1", "email": "test@example.com", "is_admin": False},
            expires_delta=timedelta(seconds=-1)
        )
        
        response = await client.get(
            "/api/v1/admin/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_malformed_token_rejected(self, client: AsyncClient):
        """Test that malformed tokens are rejected."""
        response = await client.get(
            "/api/v1/admin/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt.token"}
        )
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_wrong_auth_scheme_rejected(self, client: AsyncClient):
        """Test that wrong authentication scheme is rejected."""
        response = await client.get(
            "/api/v1/admin/auth/me",
            headers={"Authorization": "Basic dXNlcjpwYXNz"}
        )
        
        assert response.status_code in [401, 403]
