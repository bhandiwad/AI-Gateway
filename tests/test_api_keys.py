"""
API Key management tests for AI Gateway.
Tests for creating, listing, revoking, and using API keys.
"""
import pytest
from httpx import AsyncClient


class TestAPIKeyCreation:
    """Tests for API key creation."""
    
    @pytest.mark.asyncio
    async def test_create_api_key_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test successful API key creation."""
        response = await client.post(
            "/api/v1/admin/api-keys",
            json={
                "name": "Test API Key",
                "description": "Key for testing"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["api_key"].startswith("sk-gw-")
        assert data["name"] == "Test API Key"
        assert data["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_create_api_key_with_environment(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test API key creation with environment specification."""
        response = await client.post(
            "/api/v1/admin/api-keys",
            json={
                "name": "Dev Key",
                "description": "Development key",
                "environment": "development"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["environment"] == "development"
    
    @pytest.mark.asyncio
    async def test_create_api_key_with_rate_limit(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test API key creation with rate limit override."""
        response = await client.post(
            "/api/v1/admin/api-keys",
            json={
                "name": "Rate Limited Key",
                "rate_limit_override": 50
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rate_limit_override"] == 50
    
    @pytest.mark.asyncio
    async def test_create_api_key_without_auth_fails(self, client: AsyncClient):
        """Test API key creation without authentication fails."""
        response = await client.post(
            "/api/v1/admin/api-keys",
            json={"name": "Unauthorized Key"}
        )
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_create_api_key_missing_name_fails(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test API key creation without name fails."""
        response = await client.post(
            "/api/v1/admin/api-keys",
            json={"description": "No name provided"},
            headers=auth_headers
        )
        
        assert response.status_code == 422


class TestAPIKeyListing:
    """Tests for API key listing."""
    
    @pytest.mark.asyncio
    async def test_list_api_keys_empty(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing API keys when none exist."""
        response = await client.get(
            "/api/v1/admin/api-keys",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_list_api_keys_with_keys(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing API keys after creating some."""
        await client.post(
            "/api/v1/admin/api-keys",
            json={"name": "Key 1"},
            headers=auth_headers
        )
        await client.post(
            "/api/v1/admin/api-keys",
            json={"name": "Key 2"},
            headers=auth_headers
        )
        
        response = await client.get(
            "/api/v1/admin/api-keys",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    @pytest.mark.asyncio
    async def test_list_api_keys_does_not_expose_full_key(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that listing keys doesn't expose full API key."""
        create_response = await client.post(
            "/api/v1/admin/api-keys",
            json={"name": "Secret Key"},
            headers=auth_headers
        )
        full_key = create_response.json()["api_key"]
        
        list_response = await client.get(
            "/api/v1/admin/api-keys",
            headers=auth_headers
        )
        
        data = list_response.json()
        for key in data:
            assert full_key not in str(key)
            assert "key_prefix" in key


class TestAPIKeyRevocation:
    """Tests for API key revocation."""
    
    @pytest.mark.asyncio
    async def test_revoke_api_key_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test successful API key revocation."""
        create_response = await client.post(
            "/api/v1/admin/api-keys",
            json={"name": "Key to Revoke"},
            headers=auth_headers
        )
        key_id = create_response.json()["id"]
        
        revoke_response = await client.delete(
            f"/api/v1/admin/api-keys/{key_id}",
            headers=auth_headers
        )
        
        assert revoke_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_revoke_nonexistent_key_fails(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test revoking non-existent key fails."""
        response = await client.delete(
            "/api/v1/admin/api-keys/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_revoked_key_not_in_list(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that revoked keys are not listed as active."""
        create_response = await client.post(
            "/api/v1/admin/api-keys",
            json={"name": "Revoked Key"},
            headers=auth_headers
        )
        key_id = create_response.json()["id"]
        
        await client.delete(
            f"/api/v1/admin/api-keys/{key_id}",
            headers=auth_headers
        )
        
        list_response = await client.get(
            "/api/v1/admin/api-keys",
            headers=auth_headers
        )
        
        active_keys = [k for k in list_response.json() if k.get("is_active")]
        assert not any(k["id"] == key_id for k in active_keys)


class TestAPIKeyAuthentication:
    """Tests for authenticating with API keys."""
    
    @pytest.mark.asyncio
    async def test_chat_with_valid_api_key(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test chat completion with valid API key."""
        create_response = await client.post(
            "/api/v1/admin/api-keys",
            json={"name": "Chat Key"},
            headers=auth_headers
        )
        api_key = create_response.json()["api_key"]
        
        chat_response = await client.post(
            "/api/v1/chat/completions",
            json={
                "model": "mock-gpt-4",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert chat_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_chat_with_invalid_api_key_fails(self, client: AsyncClient):
        """Test chat completion with invalid API key fails."""
        response = await client.post(
            "/api/v1/chat/completions",
            json={
                "model": "mock-gpt-4",
                "messages": [{"role": "user", "content": "Hello"}]
            },
            headers={"Authorization": "Bearer sk-gw-invalid-key"}
        )
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_chat_with_revoked_key_fails(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test chat completion with revoked API key fails."""
        create_response = await client.post(
            "/api/v1/admin/api-keys",
            json={"name": "Revoked Chat Key"},
            headers=auth_headers
        )
        api_key = create_response.json()["api_key"]
        key_id = create_response.json()["id"]
        
        await client.delete(
            f"/api/v1/admin/api-keys/{key_id}",
            headers=auth_headers
        )
        
        chat_response = await client.post(
            "/api/v1/chat/completions",
            json={
                "model": "mock-gpt-4",
                "messages": [{"role": "user", "content": "Hello"}]
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert chat_response.status_code in [401, 403]


class TestAPIKeyPermissions:
    """Tests for API key permission restrictions."""
    
    @pytest.mark.asyncio
    async def test_api_key_with_model_restriction(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test API key with allowed models restriction."""
        response = await client.post(
            "/api/v1/admin/api-keys",
            json={
                "name": "Restricted Models Key",
                "allowed_models_override": ["gpt-3.5-turbo"]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["allowed_models_override"] == ["gpt-3.5-turbo"]
    
    @pytest.mark.asyncio
    async def test_api_key_with_cost_limit(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test API key with cost limits."""
        response = await client.post(
            "/api/v1/admin/api-keys",
            json={
                "name": "Cost Limited Key",
                "cost_limit_daily": 10.0,
                "cost_limit_monthly": 100.0
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["cost_limit_daily"] == 10.0
        assert data["cost_limit_monthly"] == 100.0
