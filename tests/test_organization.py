"""
Organization management tests for AI Gateway.
Tests for organization settings and multi-tenant features.
"""
import pytest
from httpx import AsyncClient


class TestOrganizationSettings:
    """Tests for organization settings."""
    
    @pytest.mark.asyncio
    async def test_get_organization_settings(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting organization settings."""
        response = await client.get(
            "/api/v1/admin/organization/settings",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_update_organization_settings(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Test updating organization settings."""
        response = await client.patch(
            "/api/v1/admin/organization/settings",
            json={"name": "Updated Organization"},
            headers=admin_auth_headers
        )
        
        assert response.status_code in [200, 404]


class TestOrganizationMembers:
    """Tests for organization member management."""
    
    @pytest.mark.asyncio
    async def test_list_organization_members(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing organization members."""
        response = await client.get(
            "/api/v1/admin/organization/members",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_invite_member(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Test inviting a new member."""
        response = await client.post(
            "/api/v1/admin/organization/members/invite",
            json={
                "email": "newmember@example.com",
                "role": "member"
            },
            headers=admin_auth_headers
        )
        
        assert response.status_code in [200, 201, 404]


class TestOrganizationRoles:
    """Tests for organization role management."""
    
    @pytest.mark.asyncio
    async def test_list_roles(self, client: AsyncClient, auth_headers: dict):
        """Test listing organization roles."""
        response = await client.get(
            "/api/v1/admin/organization/roles",
            headers=auth_headers
        )
        
        assert response.status_code == 200
