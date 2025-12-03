# AI Gateway

Enterprise-grade AI Gateway for BFSI (Banking, Financial Services, Insurance) with multi-provider routing, advanced guardrails, and comprehensive billing analytics.

> **Full Documentation**: See [docs/AI_GATEWAY_DOCUMENTATION.md](docs/AI_GATEWAY_DOCUMENTATION.md) for complete technical documentation including F5 comparison, API reference, test users, and implementation details.

## Overview

This is a full-stack AI Gateway application that provides:
- Unified API for multiple AI providers (OpenAI, Anthropic, Gemini, local models)
- Multi-tenant architecture with per-user management and billing
- Advanced guardrails using NVIDIA NeMo Guardrails for BFSI compliance
- Comprehensive audit logging for regulatory compliance
- Per-user usage tracking and billing reports
- React-based admin dashboard with mobile-responsive design

## Architecture

### Backend (Python/FastAPI)
- **Location**: `backend/`
- **Framework**: FastAPI with SQLAlchemy ORM
- **Key Services**:
  - `router_service.py`: LiteLLM-based multi-provider routing
  - `nemo_guardrails_service.py`: Advanced BFSI guardrails (PII, financial advice, regulatory compliance)
  - `guardrails_service.py`: Input/output validation (PII, toxicity, prompt injection)
  - `tenancy_service.py`: Multi-tenant management and API key handling
  - `usage_service.py`: Usage logging and analytics
  - `user_service.py`: Per-user management within tenants
  - `audit_service.py`: Comprehensive audit logging for compliance
  - `billing_service.py`: Per-user billing reports and invoice generation
  - `sso_service.py`: Enterprise SSO/OIDC authentication with PKCE support
  - `semantic_cache_service.py`: Semantic caching with vector similarity (30-50% cost reduction)
  - `content_routing_service.py`: Content-based model routing with topic detection
  - `stream_inspection_service.py`: Real-time streaming response inspection
- **Telemetry**: `backend/app/telemetry/` - OpenTelemetry integration for metrics, traces, logs

### Frontend (React/Vite)
- **Location**: `ui/`
- **Framework**: React 18 with Vite and Tailwind CSS
- **Mobile-First Design**: Responsive layouts with 44-48px touch targets
- **Key Pages**:
  - Dashboard: Usage statistics and analytics
  - Models: Available AI model catalog
  - Playground: Interactive API testing
  - API Keys: Key management
  - Users: Per-user management
  - Billing: Usage reports and invoices
  - Audit Logs: Compliance audit trails
  - Guardrails: Policy configuration

### Database
- PostgreSQL with SQLAlchemy models
- Tables: tenants, api_keys, usage_logs, users, audit_logs, policies, provider_configs, sso_configs

### Configuration
- `backend/configs/models.yaml`: Model definitions and pricing
- `backend/configs/providers.yaml`: Provider configurations
- `backend/configs/guardrails.yaml`: Safety policies
- `backend/configs/routing_rules.yaml`: Routing strategies

## Running the Application

### Development
The application runs on port 5000 (frontend) with API proxy to port 8000 (backend).

```bash
# Backend
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd ui && npm run dev
```

### Production (Docker)
```bash
docker-compose up --build
```

## API Endpoints

### AI Endpoints
- `POST /api/v1/chat/completions` - Chat completions
- `POST /api/v1/embeddings` - Text embeddings
- `GET /api/v1/models` - List available models

### Admin Endpoints
- `POST /api/v1/admin/auth/register` - Register new tenant
- `POST /api/v1/admin/auth/login` - Login
- `GET /api/v1/admin/usage/dashboard` - Usage statistics
- `POST /api/v1/admin/api-keys` - Create API key

### User Management Endpoints
- `GET /api/v1/admin/users` - List users in tenant
- `POST /api/v1/admin/users` - Create user
- `GET /api/v1/admin/users/{user_id}` - Get user details
- `PUT /api/v1/admin/users/{user_id}` - Update user
- `DELETE /api/v1/admin/users/{user_id}` - Delete user
- `GET /api/v1/admin/users/{user_id}/usage` - Get user usage summary

### Audit Log Endpoints
- `GET /api/v1/admin/audit/logs` - List audit logs
- `GET /api/v1/admin/audit/summary` - Get audit summary
- `POST /api/v1/admin/audit/export` - Export audit logs
- `GET /api/v1/admin/audit/security-events` - Get security events

### Billing Endpoints
- `GET /api/v1/admin/billing/summary` - Get billing summary
- `GET /api/v1/admin/billing/user/{user_id}` - Get user billing details
- `POST /api/v1/admin/billing/invoice` - Generate invoice
- `GET /api/v1/admin/billing/export/csv` - Export usage to CSV
- `GET /api/v1/admin/billing/forecast` - Get cost forecast

### Guardrails Endpoints
- `GET /api/v1/admin/guardrails` - List available guardrails
- `GET /api/v1/admin/guardrails/policies` - List policy templates
- `POST /api/v1/admin/guardrails/test` - Test guardrails on text
- `GET /api/v1/admin/guardrails/bfsi` - Get BFSI-specific guardrails
- `PUT /api/v1/admin/guardrails/policy` - Update tenant policy

### SSO Endpoints
- `GET /api/v1/admin/auth/sso/providers` - List enabled SSO providers
- `POST /api/v1/admin/auth/sso/initiate` - Initiate SSO login flow
- `GET /api/v1/admin/auth/sso/callback` - Handle SSO callback
- `GET /api/v1/admin/sso/config` - Get tenant SSO configuration
- `POST /api/v1/admin/sso/config` - Create SSO configuration
- `PUT /api/v1/admin/sso/config` - Update SSO configuration
- `POST /api/v1/admin/sso/discover` - Discover OIDC provider configuration

## BFSI Compliance Features

### Guardrails
- **PII Detection**: Detects and redacts SSN, credit cards, bank accounts, Aadhaar, PAN
- **Financial Advice Guard**: Flags investment recommendations and financial advice
- **Prompt Injection Detection**: Blocks manipulation attempts
- **Jailbreak Detection**: Prevents AI safety bypass attempts
- **Toxicity Filter**: Blocks harmful content
- **Confidential Data Protection**: Prevents disclosure of proprietary information

### Audit Logging
- Login/logout tracking
- API request logging
- Configuration changes
- Guardrail triggers
- Data exports
- Security events

### Billing Model
- Per-user pricing: Fixed rate per active user
- Token costs: Pay-per-use for AI model tokens
- Invoice generation with line items
- Usage export (CSV)
- Cost forecasting

## Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string
- `SESSION_SECRET` - JWT signing secret

Optional:
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `REDIS_URL` - Redis URL for rate limiting and SSO state

## User Preferences

- Using Python 3.11+ with FastAPI
- React 18 with Vite and Tailwind CSS
- PostgreSQL for data persistence
- LiteLLM for multi-provider routing
- NVIDIA NeMo Guardrails for advanced safety
- Mobile-first responsive design

## Role-Based Access Control (RBAC)

The gateway implements enterprise-grade RBAC with 4 user roles:

### Roles and Permissions

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| **Admin** | Full system access | All permissions including user deletion, guardrails editing, settings modification |
| **Manager** | Operational access | Create API keys, view billing, manage users, view audit logs, test guardrails |
| **User** | Gateway consumers | Use AI gateway, view dashboard, view own API keys |
| **Viewer** | Read-only access | View dashboard, billing, audit logs, guardrails, router config |

### Permission Categories
- `api_keys:*` - API key management (view, create, revoke)
- `billing:*` - Billing access (view, export, invoice)
- `audit:*` - Audit log access (view, export)
- `users:*` - User management (view, create, edit, delete)
- `guardrails:*` - Guardrail config (view, edit, test)
- `router:*` - Router config (view, edit)
- `gateway:use` - Use AI gateway APIs
- `dashboard:view` - View dashboard
- `settings:*` - Settings management (view, edit)

### Implementation
- Backend: `backend/app/core/permissions.py` - Permission decorators and role matrix
- Frontend: `ui/src/contexts/AuthContext.jsx` - Permission hooks (hasPermission, hasAnyPermission)
- Navigation: Sidebar shows/hides menu items based on user permissions

## Enterprise Features (F5 AI Gateway Parity)

### 1. OpenTelemetry Integration
- Full metrics export: LLM requests, token counts, latency, costs
- Distributed tracing with span creation for request lifecycle
- OTLP exporter support for Datadog, Grafana, New Relic
- TelemetryMiddleware for HTTP request instrumentation
- Environment: `OTLP_ENDPOINT` for exporter configuration

### 2. Semantic Caching (30-50% Cost Reduction)
- Vector similarity search using cosine similarity (0.92 threshold)
- Redis backend with in-memory fallback
- Per-tenant cache isolation
- Automatic embedding generation for prompt comparison
- Endpoints: `GET /api/v1/cache/stats`, `DELETE /api/v1/cache`

### 3. Content-Based Model Routing
- 10 content categories: coding, creative, analysis, math, financial, legal, medical, technical, customer_service, general
- Pattern-based topic detection with confidence scoring
- Automatic model selection based on content type (e.g., coding → Claude, creative → GPT-4)
- Per-tenant routing overrides
- Endpoint: `GET /api/v1/routing/config`

### 4. Streaming Response Inspection
- Real-time guardrail inspection during streaming responses
- Configurable inspection intervals (default: every 10 chunks)
- Buffer management with chunk tracking
- Immediate blocking of violating content mid-stream
- Violation callbacks for logging

### Feature Configuration
```python
ENABLE_TELEMETRY: bool = True
OTLP_ENDPOINT: Optional[str] = None
ENABLE_SEMANTIC_CACHE: bool = True
SEMANTIC_CACHE_SIMILARITY_THRESHOLD: float = 0.92
ENABLE_CONTENT_ROUTING: bool = True
ENABLE_STREAM_INSPECTION: bool = True
```

### Custom Model Management Endpoints
- `POST /api/v1/admin/models/custom` - Create custom model
- `PUT /api/v1/admin/models/custom/{model_id}` - Update custom model
- `DELETE /api/v1/admin/models/custom/{model_id}` - Delete custom model
- `GET /api/v1/admin/models/settings` - List all models (built-in + custom)
- `PUT /api/v1/admin/models/{model_id}/toggle` - Enable/disable model
- `POST /api/v1/admin/models/reorder` - Reorder model display order

### Router Configuration Endpoints
- `GET /api/v1/admin/router/config` - Get current routing configuration
- `PUT /api/v1/admin/router/config` - Update routing configuration
- `GET /api/v1/admin/router/providers` - List available providers

## Recent Changes

- **Added Router Settings UI** - Editable rate limit tiers, max retries, fallback order, and default provider configuration with drag-and-drop reordering
- **Added Custom Model Management** - Tenants can add, edit, and delete custom AI models with full configuration (provider, pricing, context length, capabilities)
- INR currency display across all pages (₹ symbol with 83.5 conversion rate)
- Neutral enterprise UI palette (white/gray/slate) with no colorful gradients
- Model Catalog now shows all 31 models with Add/Edit/Delete functionality
- **Added 4 Enterprise Features** matching F5 AI Gateway capabilities
- OpenTelemetry integration with OTLP export support
- Semantic caching for 30-50% LLM cost reduction
- Content-based model routing with topic detection
- Streaming response inspection for real-time guardrails
- **Implemented RBAC system** with role-based permissions for all admin endpoints
- Added permission decorators for backend route protection
- Frontend AuthContext now includes role and permissions from /auth/me endpoint
- Sidebar navigation hides pages user doesn't have permission to access
- User role badge displayed in sidebar
- Added User management system with roles (admin, manager, user, viewer)
- Added per-user usage tracking for billing
- Implemented comprehensive audit logging with recursive PII sanitization
- Integrated NVIDIA NeMo Guardrails for BFSI compliance
- Added billing reports API with invoice generation and cost forecasting
- Fixed NULL handling in billing queries with COALESCE for JSON serialization
- Users now default to ACTIVE status for immediate authentication (both SSO and password-based)
- Enhanced audit exports with full BFSI identifier coverage (Aadhaar, PAN, bank accounts, etc.)
- IPv6 addresses fully masked as [IPv6_MASKED] to prevent network prefix leakage
