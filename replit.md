# AI Gateway

Enterprise-grade AI Gateway for BFSI (Banking, Financial Services, Insurance) with multi-provider routing, advanced guardrails, and comprehensive billing analytics.

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

## Recent Changes

- Added User management system with roles (admin, manager, user, viewer)
- Added per-user usage tracking for billing
- Implemented comprehensive audit logging with recursive PII sanitization
- Integrated NVIDIA NeMo Guardrails for BFSI compliance
- Added billing reports API with invoice generation and cost forecasting
- Fixed NULL handling in billing queries with COALESCE for JSON serialization
- Users now default to ACTIVE status for immediate authentication (both SSO and password-based)
- Enhanced audit exports with full BFSI identifier coverage (Aadhaar, PAN, bank accounts, etc.)
- IPv6 addresses fully masked as [IPv6_MASKED] to prevent network prefix leakage
