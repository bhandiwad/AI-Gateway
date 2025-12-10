# AI Gateway

## Overview

The AI Gateway is an enterprise-grade, full-stack application providing a unified, secure, and compliant interface for accessing diverse AI models. Its core purpose is to offer multi-provider AI model routing, advanced guardrails for regulatory compliance (e.g., PII protection), and a multi-tenant architecture with per-user management and billing. The project emphasizes cost reduction through features like semantic caching and intelligent content-based routing, alongside an intuitive admin dashboard for comprehensive management and analytics. It aims to streamline AI model consumption, enhance security, and provide granular control and visibility for organizations.

## User Preferences

- Using Python 3.11+ with FastAPI
- React 18 with Vite and Tailwind CSS
- PostgreSQL for data persistence
- LiteLLM for multi-provider routing
- NVIDIA NeMo Guardrails for advanced safety
- Mobile-first responsive design
- INR currency display (₹ symbol with 83.5 conversion rate)
- **InfinitAI branding** with green/lime color theme (lime-500, lime-600, green-500)
- White sidebar with green accent colors for navigation

## System Architecture

The AI Gateway comprises a Python/FastAPI backend and a React/Vite frontend, communicating with a PostgreSQL database.

### Backend (Python/FastAPI)
- **Location**: `backend/`
- **Framework**: FastAPI with SQLAlchemy ORM
- **Port**: 8000
- **Key Services**:
    - Multi-provider routing (`router_service.py`)
    - Advanced enterprise guardrails (`nemo_guardrails_service.py`, `guardrails_service.py`)
    - Multi-tenant, user, and API key management (`tenancy_service.py`, `user_service.py`)
    - Usage logging, billing, and audit trails (`usage_service.py`, `billing_service.py`, `audit_service.py`)
    - Enterprise SSO/OIDC authentication (`sso_service.py`)
    - Semantic caching and content-based routing (`semantic_cache_service.py`, `content_routing_service.py`)
    - Real-time streaming response inspection (`stream_inspection_service.py`)
    - F5-style provider and router configuration management (`provider_config_service.py`)
- **Telemetry**: OpenTelemetry integration for monitoring.

### Frontend (React/Vite)
- **Location**: `ui/`
- **Framework**: React 18 with Vite and Tailwind CSS
- **Port**: 5000
- **Key Pages**: Dashboard (merged with Health & Reliability as tabs), Models, Playground, API Keys, Users, Organization, Alerts, Billing, Audit Logs, Guardrails, External Guardrails, Router Config.
- **Branding**: InfinitAI with custom infinity-style logo in green/lime colors
- **UI/UX Decisions**: 
  - Mobile-first responsive design
  - White sidebar with green/lime accent colors
  - Dashboard with tabs for Overview and Health & Reliability
  - Navigation order: Dashboard, Router, Models, Playground, Guardrails, External Guardrails, API Keys, Users, Organization, Alerts, Billing, Audit Logs, Tenants (admin only), Settings
- **Shared Components**: `InfinitAILogo` component in `ui/src/components/InfinitAILogo.jsx`

### Database Schema
PostgreSQL is used for data persistence with tables for `tenants`, `api_keys`, `usage_logs`, `users`, `audit_logs`, `policies`, `provider_configs`, `guardrail_profiles`, `api_routes`, and `sso_configs`.

### F5-Style Configuration System
A core architectural decision is the F5-style configuration system, enabling granular control over AI Gateway behavior:
-   **Provider Configuration**: Multi-step wizard for defining and managing AI model providers (e.g., OpenAI, Azure) with detailed connection, authentication, rate limiting, and traffic classification settings.
-   **API Route Management**: Custom route creation with per-route policies, rate limits, and model/provider assignments. Includes allowed_models enforcement at runtime.
-   **Unified Guardrail Profiles**: Centralized management of guardrail configurations as "profiles" consisting of ordered chains of request and response processors (e.g., PII detection, toxicity filtering, prompt injection detection). These profiles are assignable at tenant, API key, and API route levels.
-   **Enhanced Tenant and API Key Management**: Extended models for tenants and API keys to include F5-style controls such as default guardrail profiles, spend limits, logging policies, and allowed providers/models. Includes validation to prevent cross-tenant resource exposure.

### Hierarchical Guardrail Resolution
The GuardrailResolver service (`backend/app/services/guardrail_resolver.py`) implements hierarchical profile resolution:
1. **Route Level**: If the API route has `profile_id` set, use that profile
2. **API Key Level**: If the API key has `guardrail_profile_id` set, use that profile  
3. **Team Level**: If the API key's team has `guardrail_profile_id` set, use that profile
4. **Department Level**: If the team's department has `guardrail_profile_id` set, use that profile
5. **Tenant Level**: If the tenant has `guardrail_profile_id` set, use that profile
6. **System Default**: Fall back to system default profile

The ProfileGuardrailsService (`backend/app/services/profile_guardrails_service.py`) executes processor chains with actions: allow, block, redact, warn.

### External Guardrail Provider Integration
External guardrail providers (OpenAI Moderation, AWS Comprehend, Azure Content Safety, Google NLP) are integrated as processor types within guardrail profiles:
- **Processor Type**: `external_provider` with config containing `provider_type` and `provider_name`
- **Supported Providers**: openai, aws_comprehend, azure_content_safety, google_nlp
- **Async Execution**: External provider checks execute asynchronously via GuardrailProviderManager (`backend/app/services/guardrail_provider_manager.py`)
- **UI Configuration**: PolicyDesigner component allows adding external providers to processor chains with action selection (block/warn/allow)

### Runtime Model Enforcement
API routes can define `allowed_models` list. The chat completion endpoint (`routes_chat.py`) enforces this at runtime, rejecting requests for disallowed models with HTTP 403.

### Granular Budget Policy System
The budget policy system (`backend/app/services/budget_enforcement_service.py`) provides fine-grained cost control:

#### Budget Scopes (Most to Least Specific)
1. **Model**: Per-model spending limits (e.g., "$100/month on GPT-4")
2. **Route**: Per-API-route spending limits
3. **API Key**: Per-key spending limits
4. **User**: Per-user spending limits
5. **Team**: Per-team spending limits
6. **Department**: Per-department spending limits
7. **Tenant**: Tenant-wide spending limits
8. **Global**: System-wide spending limits

#### Key Features
- **Disabled by Default**: All budget policies are created with `enabled=false` - must be explicitly enabled
- **Hierarchical Resolution**: Checks from most specific scope to least specific, stopping at first enabled policy
- **Runtime Enforcement**: Integrated into chat completion endpoint, returns HTTP 402 when budget exceeded
- **Model Overrides**: Each policy can have model-specific limit overrides
- **Alert Thresholds**: Configurable warning thresholds (e.g., alert at 80% utilization)
- **Period Support**: Daily, weekly, monthly, or yearly budget periods

#### Database Models
- `BudgetPolicy`: Stores policy configuration (scope, limit, period, enabled flag)
- `BudgetUsageSnapshot`: Tracks current spend per policy for quick lookups

#### API Endpoints
- `GET /api/v1/budgets`: List all budget policies
- `POST /api/v1/budgets`: Create new budget policy
- `PUT /api/v1/budgets/{id}`: Update budget policy
- `DELETE /api/v1/budgets/{id}`: Delete budget policy
- `POST /api/v1/budgets/{id}/toggle`: Enable/disable budget policy

#### UI Component
The `BudgetPolicies` component in the Billing page provides:
- Policy creation with scope/limit/period configuration
- Real-time utilization display with progress bars
- Enable/disable toggle for each policy
- Edit and delete functionality

## External Dependencies

-   **AI Providers**: OpenAI, Anthropic, Gemini (integrated via LiteLLM)
-   **Guardrails**: NVIDIA NeMo Guardrails
-   **Database**: PostgreSQL
-   **Caching**: Redis (for rate limiting, SSO state, semantic cache)
-   **Authentication**: OIDC (for SSO)
-   **Monitoring**: OpenTelemetry
-   **Frontend Libraries**: React 18, Vite, Tailwind CSS, @hello-pangea/dnd
-   **Backend Libraries**: FastAPI, SQLAlchemy, LiteLLM, Uvicorn