"""
Router and provider configuration tests for AI Gateway.
Tests for routing configuration, provider management, and load balancing.
"""
import pytest
from httpx import AsyncClient


class TestRouterConfiguration:
    """Tests for router configuration endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_router_config(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting router configuration."""
        response = await client.get(
            "/api/v1/admin/router/config",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "default_provider" in data
        assert "default_model" in data
        assert "strategies" in data
    
    @pytest.mark.asyncio
    async def test_router_config_has_strategies(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that router config includes routing strategies."""
        response = await client.get(
            "/api/v1/admin/router/config",
            headers=auth_headers
        )
        
        data = response.json()
        strategies = data["strategies"]
        assert isinstance(strategies, list)
        assert len(strategies) > 0
        
        for strategy in strategies:
            assert "name" in strategy
            assert "description" in strategy
    
    @pytest.mark.asyncio
    async def test_router_config_has_fallback(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that router config includes fallback settings."""
        response = await client.get(
            "/api/v1/admin/router/config",
            headers=auth_headers
        )
        
        data = response.json()
        assert "fallback" in data
        fallback = data["fallback"]
        assert "enabled" in fallback
        assert "max_retries" in fallback
    
    @pytest.mark.asyncio
    async def test_router_config_has_rate_limit_tiers(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that router config includes rate limit tiers."""
        response = await client.get(
            "/api/v1/admin/router/config",
            headers=auth_headers
        )
        
        data = response.json()
        assert "rate_limit_tiers" in data
        tiers = data["rate_limit_tiers"]
        assert isinstance(tiers, list)


class TestProviderManagement:
    """Tests for provider management endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_providers(self, client: AsyncClient, auth_headers: dict):
        """Test listing providers."""
        response = await client.get(
            "/api/v1/admin/router/providers",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert isinstance(data["providers"], list)
    
    @pytest.mark.asyncio
    async def test_providers_have_required_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that providers have required fields."""
        response = await client.get(
            "/api/v1/admin/router/providers",
            headers=auth_headers
        )
        
        data = response.json()
        for provider in data["providers"]:
            assert "name" in provider
            assert "type" in provider
            assert "is_active" in provider
            assert "models" in provider
    
    @pytest.mark.asyncio
    async def test_providers_include_openai(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that OpenAI provider is configured."""
        response = await client.get(
            "/api/v1/admin/router/providers",
            headers=auth_headers
        )
        
        data = response.json()
        provider_names = [p["name"] for p in data["providers"]]
        assert "openai" in provider_names
    
    @pytest.mark.asyncio
    async def test_providers_include_anthropic(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that Anthropic provider is configured."""
        response = await client.get(
            "/api/v1/admin/router/providers",
            headers=auth_headers
        )
        
        data = response.json()
        provider_names = [p["name"] for p in data["providers"]]
        assert "anthropic" in provider_names
    
    @pytest.mark.asyncio
    async def test_provider_health_check(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test provider health check endpoint."""
        response = await client.get(
            "/api/v1/admin/router/health",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestRoutingStrategies:
    """Tests for routing strategy selection."""
    
    @pytest.mark.asyncio
    async def test_cost_optimized_strategy_exists(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that cost optimized strategy exists."""
        response = await client.get(
            "/api/v1/admin/router/config",
            headers=auth_headers
        )
        
        data = response.json()
        strategy_names = [s["name"] for s in data["strategies"]]
        assert "cost_optimized" in strategy_names
    
    @pytest.mark.asyncio
    async def test_quality_first_strategy_exists(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that quality first strategy exists."""
        response = await client.get(
            "/api/v1/admin/router/config",
            headers=auth_headers
        )
        
        data = response.json()
        strategy_names = [s["name"] for s in data["strategies"]]
        assert "quality_first" in strategy_names
    
    @pytest.mark.asyncio
    async def test_balanced_strategy_exists(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that balanced strategy exists."""
        response = await client.get(
            "/api/v1/admin/router/config",
            headers=auth_headers
        )
        
        data = response.json()
        strategy_names = [s["name"] for s in data["strategies"]]
        assert "balanced" in strategy_names


class TestRoutingStatistics:
    """Tests for routing statistics endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_routing_stats(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting routing statistics."""
        response = await client.get(
            "/api/v1/admin/router/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestModelSettings:
    """Tests for model settings management."""
    
    @pytest.mark.asyncio
    async def test_get_model_settings(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting model settings."""
        response = await client.get(
            "/api/v1/admin/router/models",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestLoadBalancer:
    """Tests for load balancer functionality."""
    
    @pytest.mark.asyncio
    async def test_get_load_balancer_config(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting load balancer configuration."""
        response = await client.get(
            "/api/v1/admin/router/load-balancer",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_load_balancer_stats(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting load balancer statistics."""
        response = await client.get(
            "/api/v1/admin/router/load-balancer/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""
    
    @pytest.mark.asyncio
    async def test_get_circuit_breaker_status(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting circuit breaker status."""
        response = await client.get(
            "/api/v1/admin/router/circuit-breaker",
            headers=auth_headers
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_circuit_breaker_metrics(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting circuit breaker metrics."""
        response = await client.get(
            "/api/v1/admin/router/circuit-breaker/metrics",
            headers=auth_headers
        )
        
        assert response.status_code == 200
