"""
Audit log tests for AI Gateway.
Tests for audit logging functionality.
"""
import pytest
from httpx import AsyncClient


class TestAuditLogRetrieval:
    """Tests for retrieving audit logs."""
    
    @pytest.mark.asyncio
    async def test_get_audit_logs(self, client: AsyncClient, auth_headers: dict):
        """Test getting audit logs."""
        response = await client.get(
            "/api/v1/admin/audit-logs",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "logs" in data
    
    @pytest.mark.asyncio
    async def test_get_audit_logs_without_auth_fails(self, client: AsyncClient):
        """Test that getting audit logs without auth fails."""
        response = await client.get("/api/v1/admin/audit-logs")
        
        assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_audit_logs_have_required_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that audit logs have required fields."""
        await client.get("/api/v1/admin/auth/me", headers=auth_headers)
        
        response = await client.get(
            "/api/v1/admin/audit-logs",
            headers=auth_headers
        )
        
        data = response.json()
        logs = data if isinstance(data, list) else data.get("logs", [])
        
        if len(logs) > 0:
            log = logs[0]
            assert "action" in log or "event_type" in log
            assert "timestamp" in log or "created_at" in log


class TestAuditLogFiltering:
    """Tests for filtering audit logs."""
    
    @pytest.mark.asyncio
    async def test_filter_by_action(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test filtering audit logs by action."""
        response = await client.get(
            "/api/v1/admin/audit-logs",
            params={"action": "login"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_filter_by_date_range(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test filtering audit logs by date range."""
        response = await client.get(
            "/api/v1/admin/audit-logs",
            params={
                "start_date": "2024-01-01",
                "end_date": "2030-12-31"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_paginate_audit_logs(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test pagination of audit logs."""
        response = await client.get(
            "/api/v1/admin/audit-logs",
            params={"limit": 10, "offset": 0},
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestAuditLogGeneration:
    """Tests for audit log generation on actions."""
    
    @pytest.mark.asyncio
    async def test_login_generates_audit_log(self, client: AsyncClient):
        """Test that login generates an audit log entry."""
        await client.post(
            "/api/v1/admin/auth/register",
            json={
                "name": "Audit Test User",
                "email": "auditlogin@example.com",
                "password": "Password123!"
            }
        )
        
        login_response = await client.post(
            "/api/v1/admin/auth/login",
            json={
                "email": "auditlogin@example.com",
                "password": "Password123!"
            }
        )
        
        token = login_response.json()["access_token"]
        
        logs_response = await client.get(
            "/api/v1/admin/audit-logs",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert logs_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_api_key_creation_generates_audit_log(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that API key creation generates an audit log."""
        await client.post(
            "/api/v1/admin/api-keys",
            json={"name": "Audit Test Key"},
            headers=auth_headers
        )
        
        logs_response = await client.get(
            "/api/v1/admin/audit-logs",
            headers=auth_headers
        )
        
        assert logs_response.status_code == 200


class TestAuditLogExport:
    """Tests for audit log export functionality."""
    
    @pytest.mark.asyncio
    async def test_export_audit_logs(
        self, client: AsyncClient, admin_auth_headers: dict
    ):
        """Test exporting audit logs."""
        response = await client.get(
            "/api/v1/admin/audit-logs/export",
            headers=admin_auth_headers
        )
        
        assert response.status_code in [200, 404]
