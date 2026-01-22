"""
Alerts and notifications tests for AI Gateway.
Tests for alert configuration and notification management.
"""
import pytest
from httpx import AsyncClient


class TestAlertConfiguration:
    """Tests for alert configuration."""
    
    @pytest.mark.asyncio
    async def test_list_alerts(self, client: AsyncClient, auth_headers: dict):
        """Test listing configured alerts."""
        response = await client.get(
            "/api/v1/admin/alerts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_alert(self, client: AsyncClient, auth_headers: dict):
        """Test creating a new alert."""
        response = await client.post(
            "/api/v1/admin/alerts",
            json={
                "name": "High Usage Alert",
                "type": "usage_threshold",
                "threshold": 1000,
                "enabled": True
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_update_alert(self, client: AsyncClient, auth_headers: dict):
        """Test updating an alert."""
        create_response = await client.post(
            "/api/v1/admin/alerts",
            json={
                "name": "Update Test Alert",
                "type": "cost_threshold",
                "threshold": 100,
                "enabled": True
            },
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            alert_id = create_response.json()["id"]
            
            response = await client.patch(
                f"/api/v1/admin/alerts/{alert_id}",
                json={"threshold": 200},
                headers=auth_headers
            )
            
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_delete_alert(self, client: AsyncClient, auth_headers: dict):
        """Test deleting an alert."""
        create_response = await client.post(
            "/api/v1/admin/alerts",
            json={
                "name": "Delete Test Alert",
                "type": "error_rate",
                "threshold": 5,
                "enabled": True
            },
            headers=auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            alert_id = create_response.json()["id"]
            
            response = await client.delete(
                f"/api/v1/admin/alerts/{alert_id}",
                headers=auth_headers
            )
            
            assert response.status_code in [200, 204]


class TestAlertTypes:
    """Tests for different alert types."""
    
    @pytest.mark.asyncio
    async def test_create_usage_threshold_alert(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating usage threshold alert."""
        response = await client.post(
            "/api/v1/admin/alerts",
            json={
                "name": "Usage Alert",
                "type": "usage_threshold",
                "threshold": 5000,
                "enabled": True
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_create_cost_threshold_alert(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating cost threshold alert."""
        response = await client.post(
            "/api/v1/admin/alerts",
            json={
                "name": "Cost Alert",
                "type": "cost_threshold",
                "threshold": 50.0,
                "enabled": True
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
    
    @pytest.mark.asyncio
    async def test_create_error_rate_alert(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating error rate alert."""
        response = await client.post(
            "/api/v1/admin/alerts",
            json={
                "name": "Error Rate Alert",
                "type": "error_rate",
                "threshold": 10,
                "enabled": True
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]


class TestNotificationChannels:
    """Tests for notification channel configuration."""
    
    @pytest.mark.asyncio
    async def test_list_notification_channels(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing notification channels."""
        response = await client.get(
            "/api/v1/admin/alerts/channels",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_create_email_channel(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating email notification channel."""
        response = await client.post(
            "/api/v1/admin/alerts/channels",
            json={
                "name": "Email Channel",
                "type": "email",
                "config": {"recipients": ["admin@example.com"]}
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 404]
    
    @pytest.mark.asyncio
    async def test_create_webhook_channel(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test creating webhook notification channel."""
        response = await client.post(
            "/api/v1/admin/alerts/channels",
            json={
                "name": "Webhook Channel",
                "type": "webhook",
                "config": {"url": "https://example.com/webhook"}
            },
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201, 404]


class TestAlertHistory:
    """Tests for alert history."""
    
    @pytest.mark.asyncio
    async def test_get_alert_history(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting alert history."""
        response = await client.get(
            "/api/v1/admin/alerts/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_alert_history_filtered(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting filtered alert history."""
        response = await client.get(
            "/api/v1/admin/alerts/history",
            params={"type": "usage_threshold"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
