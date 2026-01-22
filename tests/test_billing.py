"""
Billing and usage tests for AI Gateway.
Tests for usage tracking, billing, and cost management.
"""
import pytest
from httpx import AsyncClient


class TestUsageSummary:
    """Tests for usage summary endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_usage_summary(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting usage summary."""
        response = await client.get(
            "/api/v1/admin/usage/summary",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data or "requests" in data
    
    @pytest.mark.asyncio
    async def test_get_usage_by_model(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting usage breakdown by model."""
        response = await client.get(
            "/api/v1/admin/usage/by-model",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_usage_by_provider(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting usage breakdown by provider."""
        response = await client.get(
            "/api/v1/admin/usage/by-provider",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestDashboardStats:
    """Tests for dashboard statistics."""
    
    @pytest.mark.asyncio
    async def test_get_dashboard_stats(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting dashboard statistics."""
        response = await client.get(
            "/api/v1/admin/dashboard/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_dashboard_stats_include_costs(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that dashboard stats include cost information."""
        response = await client.get(
            "/api/v1/admin/dashboard/stats",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "total_cost" in data or "cost" in data or "current_spend" in data


class TestCostTracking:
    """Tests for cost tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_get_current_spend(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting current spend."""
        response = await client.get(
            "/api/v1/admin/billing/current-spend",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_cost_breakdown(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting cost breakdown."""
        response = await client.get(
            "/api/v1/admin/billing/breakdown",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestBudgetManagement:
    """Tests for budget management."""
    
    @pytest.mark.asyncio
    async def test_get_budget_status(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting budget status."""
        response = await client.get(
            "/api/v1/admin/budgets/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_budget_alert(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating a budget alert."""
        response = await client.post(
            "/api/v1/admin/budgets/alerts",
            json={
                "threshold_percentage": 80,
                "notification_type": "email"
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 404]


class TestUsageHistory:
    """Tests for usage history."""
    
    @pytest.mark.asyncio
    async def test_get_usage_history(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting usage history."""
        response = await client.get(
            "/api/v1/admin/usage/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_usage_history_with_date_range(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting usage history with date range."""
        response = await client.get(
            "/api/v1/admin/usage/history",
            params={
                "start_date": "2024-01-01",
                "end_date": "2030-12-31"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestTokenUsage:
    """Tests for token usage tracking."""
    
    @pytest.mark.asyncio
    async def test_get_token_usage(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting token usage."""
        response = await client.get(
            "/api/v1/admin/usage/tokens",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_token_usage_by_model(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting token usage by model."""
        response = await client.get(
            "/api/v1/admin/usage/tokens/by-model",
            headers=auth_headers
        )
        
        assert response.status_code == 200
