"""
Tenant management tests for AI Gateway.
Tests for tenant CRUD operations and tenant settings.
"""
import pytest
from httpx import AsyncClient


class TestTenantListing:
    """Tests for tenant listing (admin only)."""
    
    @pytest.mark.asyncio
    async def test_list_tenants_as_admin(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Test listing tenants as admin."""
        response = await client.get(
            "/api/v1/admin/tenants",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_list_tenants_as_non_admin_fails(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that non-admin cannot list all tenants."""
        response = await client.get(
            "/api/v1/admin/tenants",
            headers=auth_headers
        )
        
        assert response.status_code in [403, 401]
    
    @pytest.mark.asyncio
    async def test_list_tenants_without_auth_fails(self, client: AsyncClient):
        """Test that unauthenticated request fails."""
        response = await client.get("/api/v1/admin/tenants")
        
        assert response.status_code in [401, 403]


class TestTenantRetrieval:
    """Tests for retrieving individual tenants."""
    
    @pytest.mark.asyncio
    async def test_get_own_tenant(
        self, client: AsyncClient, auth_headers: dict, test_tenant
    ):
        """Test getting own tenant details."""
        response = await client.get(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_tenant.id
        assert data["email"] == test_tenant.email
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_tenant(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Test getting non-existent tenant."""
        response = await client.get(
            "/api/v1/admin/tenants/99999",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 404


class TestTenantUpdate:
    """Tests for updating tenant settings."""
    
    @pytest.mark.asyncio
    async def test_update_own_tenant_name(
        self, client: AsyncClient, auth_headers: dict, test_tenant
    ):
        """Test updating own tenant name."""
        response = await client.patch(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            json={"name": "Updated Name"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_update_tenant_rate_limit_as_admin(
        self, client: AsyncClient, admin_auth_headers: dict, test_tenant
    ):
        """Test updating tenant rate limit as admin."""
        response = await client.patch(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            json={"rate_limit": 500},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rate_limit"] == 500
    
    @pytest.mark.asyncio
    async def test_update_tenant_budget(
        self, client: AsyncClient, admin_auth_headers: dict, test_tenant
    ):
        """Test updating tenant monthly budget."""
        response = await client.patch(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            json={"monthly_budget": 500.0},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["monthly_budget"] == 500.0
    
    @pytest.mark.asyncio
    async def test_update_tenant_allowed_models(
        self, client: AsyncClient, admin_auth_headers: dict, test_tenant
    ):
        """Test updating tenant allowed models."""
        response = await client.patch(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            json={"allowed_models": ["gpt-4", "gpt-3.5-turbo"]},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "gpt-4" in data["allowed_models"]


class TestTenantActivation:
    """Tests for tenant activation/deactivation."""
    
    @pytest.mark.asyncio
    async def test_deactivate_tenant_as_admin(
        self, client: AsyncClient, admin_auth_headers: dict, test_tenant
    ):
        """Test deactivating a tenant as admin."""
        response = await client.patch(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            json={"is_active": False},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_reactivate_tenant_as_admin(
        self, client: AsyncClient, admin_auth_headers: dict, test_tenant
    ):
        """Test reactivating a tenant as admin."""
        await client.patch(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            json={"is_active": False},
            headers=admin_auth_headers
        )
        
        response = await client.patch(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            json={"is_active": True},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True


class TestTenantLoggingPolicy:
    """Tests for tenant logging policy settings."""
    
    @pytest.mark.asyncio
    async def test_get_tenant_logging_policy(
        self, client: AsyncClient, auth_headers: dict, test_tenant
    ):
        """Test getting tenant logging policy."""
        response = await client.get(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "logging_policy" in data
    
    @pytest.mark.asyncio
    async def test_update_logging_policy(
        self, client: AsyncClient, admin_auth_headers: dict, test_tenant
    ):
        """Test updating tenant logging policy."""
        new_policy = {
            "log_requests": True,
            "log_responses": False,
            "log_pii_detected": True,
            "retention_days": 30
        }
        
        response = await client.patch(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            json={"logging_policy": new_policy},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200


class TestTenantCostCeilings:
    """Tests for tenant cost ceiling settings."""
    
    @pytest.mark.asyncio
    async def test_set_daily_cost_ceiling(
        self, client: AsyncClient, admin_auth_headers: dict, test_tenant
    ):
        """Test setting daily cost ceiling."""
        response = await client.patch(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            json={"cost_ceiling_daily": 50.0},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["cost_ceiling_daily"] == 50.0
    
    @pytest.mark.asyncio
    async def test_set_monthly_cost_ceiling(
        self, client: AsyncClient, admin_auth_headers: dict, test_tenant
    ):
        """Test setting monthly cost ceiling."""
        response = await client.patch(
            f"/api/v1/admin/tenants/{test_tenant.id}",
            json={"cost_ceiling_monthly": 500.0},
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["cost_ceiling_monthly"] == 500.0
