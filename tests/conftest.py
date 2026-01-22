"""
Pytest configuration and fixtures for AI Gateway test suite.
"""
import os
import pytest
import asyncio
from typing import Generator, AsyncGenerator, Dict, Any
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["ANTHROPIC_API_KEY"] = "test-key"

from backend.app.main import app
from backend.app.db.session import Base, get_db
from backend.app.core.security import create_access_token
from backend.app.services.tenancy_service import create_tenant
from backend.app.schemas.tenant import TenantCreate


TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def override_get_db(db: Session):
    """Override the get_db dependency."""
    def _override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_tenant_data() -> Dict[str, Any]:
    """Sample tenant data for testing."""
    return {
        "name": "Test Tenant",
        "email": "test@example.com",
        "password": "SecurePassword123!"
    }


@pytest.fixture
def admin_tenant_data() -> Dict[str, Any]:
    """Sample admin tenant data for testing."""
    return {
        "name": "Admin Tenant",
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "is_admin": True
    }


@pytest.fixture
def test_tenant(db: Session, test_tenant_data: Dict[str, Any]):
    """Create a test tenant in the database."""
    tenant_create = TenantCreate(**test_tenant_data)
    tenant = create_tenant(db, tenant_create)
    return tenant


@pytest.fixture
def admin_tenant(db: Session, admin_tenant_data: Dict[str, Any]):
    """Create an admin tenant in the database."""
    from backend.app.db.models.tenant import Tenant
    from backend.app.core.security import get_password_hash
    
    tenant = Tenant(
        name=admin_tenant_data["name"],
        email=admin_tenant_data["email"],
        password_hash=get_password_hash(admin_tenant_data["password"]),
        is_admin=True,
        is_active=True,
        rate_limit=1000,
        monthly_budget=10000.0
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def auth_token(test_tenant) -> str:
    """Create an authentication token for the test tenant."""
    return create_access_token(
        data={
            "sub": str(test_tenant.id),
            "email": test_tenant.email,
            "is_admin": test_tenant.is_admin
        }
    )


@pytest.fixture
def admin_auth_token(admin_tenant) -> str:
    """Create an authentication token for the admin tenant."""
    return create_access_token(
        data={
            "sub": str(admin_tenant.id),
            "email": admin_tenant.email,
            "is_admin": True
        }
    )


@pytest.fixture
def auth_headers(auth_token: str) -> Dict[str, str]:
    """Create authorization headers for the test tenant."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_auth_headers(admin_auth_token: str) -> Dict[str, str]:
    """Create authorization headers for the admin tenant."""
    return {"Authorization": f"Bearer {admin_auth_token}"}


@pytest.fixture
def api_key_data() -> Dict[str, Any]:
    """Sample API key data for testing."""
    return {
        "name": "Test API Key",
        "description": "API key for testing purposes",
        "environment": "development"
    }


@pytest.fixture
def chat_request_data() -> Dict[str, Any]:
    """Sample chat completion request data."""
    return {
        "model": "mock-gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }


@pytest.fixture
def guardrail_test_data() -> Dict[str, Any]:
    """Sample guardrail test data."""
    return {
        "text": "My SSN is 123-45-6789",
        "policy": "default",
        "is_input": True
    }


@pytest.fixture
def provider_config_data() -> Dict[str, Any]:
    """Sample provider configuration data."""
    return {
        "name": "test-openai",
        "display_name": "Test OpenAI",
        "service_type": "openai",
        "endpoint_url": "https://api.openai.com/v1",
        "is_active": True,
        "priority": 1,
        "models": ["gpt-4", "gpt-3.5-turbo"]
    }


class TestHelpers:
    """Helper methods for tests."""
    
    @staticmethod
    async def create_tenant_and_get_token(
        client: AsyncClient,
        email: str = "user@example.com",
        password: str = "Password123!",
        name: str = "Test User"
    ) -> tuple[Dict[str, Any], str]:
        """Create a tenant and return the response and token."""
        response = await client.post(
            "/api/v1/admin/auth/register",
            json={"name": name, "email": email, "password": password}
        )
        data = response.json()
        token = data.get("access_token", "")
        return data, token
    
    @staticmethod
    async def create_api_key(
        client: AsyncClient,
        headers: Dict[str, str],
        name: str = "Test Key"
    ) -> Dict[str, Any]:
        """Create an API key and return the response."""
        response = await client.post(
            "/api/v1/admin/api-keys",
            json={"name": name, "description": "Test key"},
            headers=headers
        )
        return response.json()


@pytest.fixture
def helpers():
    """Return test helper class."""
    return TestHelpers
