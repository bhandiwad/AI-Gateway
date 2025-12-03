# AI Gateway

Enterprise-grade AI Gateway for BFSI (Banking, Financial Services, Insurance) with multi-provider routing, advanced guardrails, and comprehensive billing analytics.

## Overview

The AI Gateway is a full-stack application designed to provide a unified, secure, and compliant interface for accessing various AI models. Its primary purpose is to serve the BFSI sector by offering robust features like multi-provider AI model routing, advanced guardrails for regulatory compliance (e.g., PII protection, financial advice flagging), multi-tenant architecture with per-user management and billing, and comprehensive audit logging. The project aims to reduce LLM costs through features like semantic caching and intelligent content-based routing while providing an intuitive admin dashboard for management and analytics.

## User Preferences

- Using Python 3.11+ with FastAPI
- React 18 with Vite and Tailwind CSS
- PostgreSQL for data persistence
- LiteLLM for multi-provider routing
- NVIDIA NeMo Guardrails for advanced safety
- Mobile-first responsive design
- INR currency display (₹ symbol with 83.5 conversion rate)
- Neutral enterprise UI palette (white/gray/slate)

## System Architecture

### Backend (Python/FastAPI)
- **Location**: `backend/`
- **Framework**: FastAPI with SQLAlchemy ORM
- **Port**: 8000
- **Key Services**:
  - `router_service.py`: LiteLLM-based multi-provider routing
  - `nemo_guardrails_service.py`: Advanced BFSI guardrails
  - `guardrails_service.py`: Input/output validation
  - `tenancy_service.py`: Multi-tenant management and API key handling
  - `usage_service.py`: Usage logging and analytics
  - `user_service.py`: Per-user management within tenants
  - `audit_service.py`: Comprehensive audit logging
  - `billing_service.py`: Per-user billing reports and invoice generation
  - `sso_service.py`: Enterprise SSO/OIDC authentication
  - `semantic_cache_service.py`: Semantic caching with vector similarity
  - `content_routing_service.py`: Content-based model routing
  - `stream_inspection_service.py`: Real-time streaming response inspection
  - `provider_config_service.py`: F5-style provider configuration management
- **Telemetry**: `backend/app/telemetry/` - OpenTelemetry integration

### Frontend (React/Vite)
- **Location**: `ui/`
- **Framework**: React 18 with Vite and Tailwind CSS
- **Port**: 5000
- **Key Pages**:
  - Dashboard: Usage statistics and analytics
  - Models: Available AI model catalog with Add/Edit/Delete
  - Playground: Interactive API testing
  - API Keys: Key management with environment tagging
  - Users: Per-user management with RBAC
  - Billing: Usage reports and invoices
  - Audit Logs: Compliance audit trails
  - Guardrails: Policy configuration
  - Router Config: F5-style configuration (Providers, Routes, Profiles)

### Database Schema
PostgreSQL with the following tables:
- `tenants` - Multi-tenant organizations
- `api_keys` - API key management with environment tagging
- `usage_logs` - Request/response logging
- `users` - Per-tenant user management
- `audit_logs` - Compliance audit trails
- `policies` - Guardrail policies
- `provider_configs` - Enhanced provider configurations
- `guardrail_profiles` - Reusable guardrail profile definitions
- `api_routes` - Custom API route configurations
- `sso_configs` - SSO/OIDC configurations

### Configuration Files
- `backend/configs/models.yaml`: Model definitions and pricing
- `backend/configs/providers.yaml`: Provider configurations
- `backend/configs/guardrails.yaml`: Safety policies
- `backend/configs/routing_rules.yaml`: Routing strategies

## Test Users

| Email | Password | Role |
|-------|----------|------|
| admin@test.com | admin123 | Admin |
| manager@test.com | manager123 | Manager |
| user@test.com | user123 | User |
| viewer@test.com | viewer123 | Viewer |

## F5-Style Configuration System

### 1. Provider Configuration (EnhancedProviderConfig)

Multi-step provider setup wizard with service-type-specific forms.

**Database Model** (`backend/app/db/models/provider_config.py`):
```python
class EnhancedProviderConfig:
    id: Integer (PK)
    tenant_id: Integer (FK to tenants, nullable for global)
    name: String - Display name
    service_type: String - openai, azure, aws_bedrock, anthropic, gemini, custom
    is_enabled: Boolean
    
    # Connection Settings
    api_endpoint: String - Base URL
    api_version: String - API version (e.g., 2024-02-15-preview)
    region: String - AWS/Azure region
    
    # Authentication
    auth_type: String - api_key, oauth, iam
    vault_secret_path: String - HashiCorp Vault path for API key
    
    # Rate Limiting
    rate_limit_rpm: Integer - Requests per minute
    rate_limit_tpm: Integer - Tokens per minute
    timeout_seconds: Integer - Request timeout
    max_retries: Integer - Retry count
    
    # Traffic Classification
    traffic_type: String - enterprise, external
    
    # Metadata
    description: Text
    tags: JSON
```

**Frontend Component** (`ui/src/components/ProviderSetupModal.jsx`):
- Step 1: Basic Info (name, service type, description)
- Step 2: Connection (endpoint, region, auth, vault path)
- Step 3: Limits (rate limits, timeout, retries)

**API Endpoints**:
- `GET /api/v1/admin/providers` - List all provider configs
- `POST /api/v1/admin/providers` - Create provider config
- `PUT /api/v1/admin/providers/{id}` - Update provider config
- `DELETE /api/v1/admin/providers/{id}` - Delete provider config

### 2. API Route Management (APIRoute)

Custom route creation with per-route policies and rate limits.

**Database Model**:
```python
class APIRoute:
    id: Integer (PK)
    tenant_id: Integer (FK)
    name: String - Route name
    path_pattern: String - e.g., /v1/chat/completions
    allowed_methods: JSON - ["POST", "GET"]
    
    # Routing
    default_provider_id: Integer (FK)
    default_model: String
    
    # Rate Limiting
    rate_limit_rpm: Integer
    rate_limit_tpm: Integer
    
    # Policy
    guardrail_profile_id: Integer (FK)
    
    # Path Manipulation
    strip_prefix: String
    add_prefix: String
    
    # Priority
    priority: Integer
    is_enabled: Boolean
```

**Frontend Component** (`ui/src/components/RouteSetupModal.jsx`):
- Route path pattern and name
- HTTP method selection (checkboxes)
- Default provider and model
- Rate limits (RPM/TPM)
- Guardrail profile assignment

**API Endpoints**:
- `GET /api/v1/admin/providers/routes` - List API routes
- `POST /api/v1/admin/providers/routes` - Create API route
- `PUT /api/v1/admin/providers/routes/{id}` - Update route
- `DELETE /api/v1/admin/providers/routes/{id}` - Delete route

### 3. Guardrail Profiles (Policy Designer)

Reusable guardrail profile definitions with processor chains.

**Database Model**:
```python
class GuardrailProfile:
    id: Integer (PK)
    tenant_id: Integer (FK, nullable for global)
    name: String
    description: Text
    is_enabled: Boolean
    
    # Processor Chains (JSON)
    request_processors: JSON - Ordered list of request processors
    response_processors: JSON - Ordered list of response processors
```

**Processor Configuration**:
```json
{
  "id": "pii_detector",
  "name": "PII Detector",
  "enabled": true,
  "config": {
    "patterns": ["ssn", "credit_card", "aadhaar", "pan"]
  }
}
```

**Built-in Processors**:
- `pii_detector` - Detects SSN, credit cards, Aadhaar, PAN, bank accounts
- `toxicity_filter` - Filters toxic/harmful content
- `prompt_injection_guard` - Detects prompt injection attempts
- `jailbreak_detector` - Detects jailbreak attempts
- `financial_advice_guard` - Flags unauthorized financial advice
- `cost_guard` - Enforces cost limits
- `rate_limiter` - Per-request rate limiting
- `content_filter` - Custom content filtering

**Frontend Component** (`ui/src/components/PolicyDesigner.jsx`):
- Request processor chain with drag-drop ordering
- Response processor chain with drag-drop ordering
- Enable/disable toggles per processor
- Move up/down controls for ordering

**API Endpoints**:
- `GET /api/v1/admin/providers/profiles` - List guardrail profiles
- `POST /api/v1/admin/providers/profiles` - Create profile
- `PUT /api/v1/admin/providers/profiles/{id}` - Update profile
- `DELETE /api/v1/admin/providers/profiles/{id}` - Delete profile

### 4. Enhanced Tenant Management

Extended tenant model with F5-style controls.

**New Tenant Fields**:
```python
class Tenant:
    # ... existing fields ...
    
    # F5-Style Additions
    guardrail_profile_id: Integer (FK) - Default guardrail profile
    default_provider_id: Integer (FK) - Default provider
    cost_ceiling_daily: Float - Daily spend limit
    cost_ceiling_monthly: Float - Monthly spend limit
    logging_policy: String - full, minimal, none
    allowed_providers: Text (JSON) - Allowed provider IDs
    allowed_models: Text (JSON) - Allowed model IDs
```

**Tenant Scoping Validation** (`tenancy_service.py`):
- `_validate_resource_ownership()` - Ensures guardrail profiles and provider configs referenced by tenants belong to the same tenant or are globally shared
- Prevents cross-tenant data exposure via resource references

### 5. Enhanced API Key Management

Extended API key model with environment tagging.

**New API Key Fields**:
```python
class APIKey:
    # ... existing fields ...
    
    # F5-Style Additions
    environment: String - dev, staging, production
    guardrail_profile_id: Integer (FK) - Per-key profile override
    provider_id: Integer (FK) - Per-key provider override
    cost_limit: Float - Per-key spend limit
```

## Router Configuration UI

The Router Config page (`ui/src/pages/RouterConfig.jsx`) now includes:

1. **Settings Tab** - General router settings, rate limits, fallback order
2. **Providers Tab** - Provider configuration management
3. **API Routes Tab** - Custom route management
4. **Guardrail Profiles Tab** - Policy designer with processor ordering

## Recent Changes (December 2024)

### F5-Style Configuration System
- Added multi-step provider setup wizard with service-type-specific forms
- Created API route management with per-route rate limits and policies
- Built Policy Designer component with drag-drop processor ordering
- Extended Tenant model with guardrail profiles, cost ceilings, logging policies
- Extended API Key model with environment tagging and per-key overrides

### Database Migrations
Added new columns to existing tables:
```sql
-- Tenants table
ALTER TABLE tenants ADD COLUMN guardrail_profile_id INTEGER;
ALTER TABLE tenants ADD COLUMN default_provider_id INTEGER;
ALTER TABLE tenants ADD COLUMN cost_ceiling_daily FLOAT;
ALTER TABLE tenants ADD COLUMN cost_ceiling_monthly FLOAT;
ALTER TABLE tenants ADD COLUMN logging_policy VARCHAR(50) DEFAULT 'full';
ALTER TABLE tenants ADD COLUMN allowed_providers TEXT;
ALTER TABLE tenants ADD COLUMN allowed_models TEXT;

-- API Keys table
ALTER TABLE api_keys ADD COLUMN environment VARCHAR(20) DEFAULT 'production';
ALTER TABLE api_keys ADD COLUMN guardrail_profile_id INTEGER;
ALTER TABLE api_keys ADD COLUMN provider_id INTEGER;
ALTER TABLE api_keys ADD COLUMN cost_limit FLOAT;
```

### Security Enhancements
- Added tenant scoping validation to prevent cross-tenant data exposure
- Resource ownership validation for guardrail profiles and provider configs
- SQLAlchemy relationship fixes for EnhancedProviderConfig

### Frontend Components
- `ProviderSetupModal.jsx` - 3-step provider configuration wizard
- `RouteSetupModal.jsx` - API route configuration modal
- `PolicyDesigner.jsx` - Drag-drop guardrail profile editor

### Backend Services
- `provider_config_service.py` - Provider configuration CRUD operations
- `routes_providers.py` - API endpoints for providers, routes, and profiles
- Enhanced `tenancy_service.py` with resource ownership validation

## External Dependencies

- **AI Providers**: OpenAI, Anthropic, Gemini (via LiteLLM)
- **Guardrails**: NVIDIA NeMo Guardrails
- **Database**: PostgreSQL
- **Caching**: Redis (optional, for rate limiting, SSO state, semantic cache)
- **Authentication**: OIDC (for SSO)
- **Monitoring**: OpenTelemetry (compatible with Datadog, Grafana, New Relic)
- **Frontend**: React 18, Vite, Tailwind CSS, @hello-pangea/dnd
- **Backend**: FastAPI, SQLAlchemy, LiteLLM, Uvicorn

## Running the Application

### Development
```bash
# Backend (port 8000)
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (port 5000)
cd ui && npm run dev
```

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `SESSION_SECRET` - JWT session secret
- `REDIS_URL` - Redis connection (optional)
- `OPENAI_API_KEY` - OpenAI API key (for LLM routing)
