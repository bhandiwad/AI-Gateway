"""
Health check and system status tests for AI Gateway.
Tests for health endpoints, metrics, and feature status.
"""
import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """Tests for health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint returns service info."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data


class TestMetrics:
    """Tests for metrics endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, client: AsyncClient):
        """Test getting metrics."""
        response = await client.get("/metrics")
        
        assert response.status_code == 200


class TestFeatureStatus:
    """Tests for feature status endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_feature_status(self, client: AsyncClient):
        """Test getting feature status."""
        response = await client.get("/api/v1/admin/features/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "telemetry" in data or "features" in data
    
    @pytest.mark.asyncio
    async def test_feature_status_includes_semantic_cache(
        self, client: AsyncClient
    ):
        """Test that feature status includes semantic cache."""
        response = await client.get("/api/v1/admin/features/status")
        
        data = response.json()
        assert "semantic_cache" in data
    
    @pytest.mark.asyncio
    async def test_feature_status_includes_load_balancing(
        self, client: AsyncClient
    ):
        """Test that feature status includes load balancing."""
        response = await client.get("/api/v1/admin/features/status")
        
        data = response.json()
        assert "load_balancing" in data
    
    @pytest.mark.asyncio
    async def test_feature_status_includes_circuit_breaker(
        self, client: AsyncClient
    ):
        """Test that feature status includes circuit breaker."""
        response = await client.get("/api/v1/admin/features/status")
        
        data = response.json()
        assert "circuit_breaker" in data


class TestOpenAPIDocumentation:
    """Tests for OpenAPI documentation."""
    
    @pytest.mark.asyncio
    async def test_docs_endpoint(self, client: AsyncClient):
        """Test Swagger UI endpoint."""
        response = await client.get("/docs")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_redoc_endpoint(self, client: AsyncClient):
        """Test ReDoc endpoint."""
        response = await client.get("/redoc")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_openapi_json(self, client: AsyncClient):
        """Test OpenAPI JSON schema endpoint."""
        response = await client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
