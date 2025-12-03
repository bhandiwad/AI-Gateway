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
- Neutral enterprise UI palette (white/gray/slate)

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
- **Key Pages**: Dashboard, Models, Playground, API Keys, Users, Billing, Audit Logs, Guardrails, and a comprehensive Router Config for providers, routes, and guardrail profiles.
- **UI/UX Decisions**: Mobile-first responsive design, neutral enterprise color palette.

### Database Schema
PostgreSQL is used for data persistence with tables for `tenants`, `api_keys`, `usage_logs`, `users`, `audit_logs`, `policies`, `provider_configs`, `guardrail_profiles`, `api_routes`, and `sso_configs`.

### F5-Style Configuration System
A core architectural decision is the F5-style configuration system, enabling granular control over AI Gateway behavior:
-   **Provider Configuration**: Multi-step wizard for defining and managing AI model providers (e.g., OpenAI, Azure) with detailed connection, authentication, rate limiting, and traffic classification settings.
-   **API Route Management**: Custom route creation with per-route policies, rate limits, and model/provider assignments.
-   **Unified Guardrail Profiles**: Centralized management of guardrail configurations as "profiles" consisting of ordered chains of request and response processors (e.g., PII detection, toxicity filtering, prompt injection detection). These profiles are assignable at tenant, API key, and API route levels.
-   **Enhanced Tenant and API Key Management**: Extended models for tenants and API keys to include F5-style controls such as default guardrail profiles, spend limits, logging policies, and allowed providers/models. Includes validation to prevent cross-tenant resource exposure.

## External Dependencies

-   **AI Providers**: OpenAI, Anthropic, Gemini (integrated via LiteLLM)
-   **Guardrails**: NVIDIA NeMo Guardrails
-   **Database**: PostgreSQL
-   **Caching**: Redis (for rate limiting, SSO state, semantic cache)
-   **Authentication**: OIDC (for SSO)
-   **Monitoring**: OpenTelemetry
-   **Frontend Libraries**: React 18, Vite, Tailwind CSS, @hello-pangea/dnd
-   **Backend Libraries**: FastAPI, SQLAlchemy, LiteLLM, Uvicorn