# AI Gateway

Enterprise-grade AI Gateway for BFSI (Banking, Financial Services, Insurance) with multi-provider routing, advanced guardrails, and comprehensive billing analytics.

### Overview

The AI Gateway is a full-stack application designed to provide a unified, secure, and compliant interface for accessing various AI models. Its primary purpose is to serve the BFSI sector by offering robust features like multi-provider AI model routing, advanced guardrails for regulatory compliance (e.g., PII protection, financial advice flagging), multi-tenant architecture with per-user management and billing, and comprehensive audit logging. The project aims to reduce LLM costs through features like semantic caching and intelligent content-based routing while providing an intuitive admin dashboard for management and analytics.

### User Preferences

- Using Python 3.11+ with FastAPI
- React 18 with Vite and Tailwind CSS
- PostgreSQL for data persistence
- LiteLLM for multi-provider routing
- NVIDIA NeMo Guardrails for advanced safety
- Mobile-first responsive design

### System Architecture

The AI Gateway is built as a full-stack application with a Python/FastAPI backend and a React/Vite frontend.

**UI/UX Decisions:**
The frontend utilizes React 18, Vite, and Tailwind CSS, adhering to a mobile-first responsive design with 44-48px touch targets. The design employs a neutral enterprise UI palette (white/gray/slate) without colorful gradients. The admin dashboard offers comprehensive views for usage statistics, model catalog, API key management, user administration, billing, audit logs, and guardrail configuration.

**Technical Implementations & Feature Specifications:**

*   **Multi-Provider Routing**: Leverages LiteLLM for unified API access to OpenAI, Anthropic, Gemini, and local models. Supports content-based routing with topic detection and custom model management.
*   **Advanced Guardrails**: Integrates NVIDIA NeMo Guardrails for BFSI-specific compliance, including PII detection (SSN, credit cards, bank accounts, Aadhaar, PAN), financial advice flagging, prompt injection, jailbreak detection, and toxicity filtering. Real-time streaming response inspection is also implemented.
*   **Multi-tenancy & User Management**: Features a multi-tenant architecture with per-user management, role-based access control (RBAC) supporting Admin, Manager, User, and Viewer roles with granular permissions, and Enterprise SSO/OIDC authentication.
*   **Billing & Usage Tracking**: Provides per-user usage tracking, comprehensive billing reports, invoice generation, cost forecasting, and usage export (CSV). Supports both fixed per-user pricing and pay-per-use token costs.
*   **Audit Logging**: Implements comprehensive audit logging for regulatory compliance, tracking logins, API requests, configuration changes, guardrail triggers, data exports, and security events with recursive PII sanitization.
*   **Semantic Caching**: Reduces LLM costs by 30-50% using vector similarity search for semantic caching, with Redis backend and per-tenant cache isolation.
*   **OpenTelemetry Integration**: Full metrics export (LLM requests, token counts, latency, costs), distributed tracing, and OTLP exporter support for various monitoring tools.
*   **F5-Style Configuration System**: Includes a multi-step provider setup wizard, API route management with per-route rate limits, and a guardrail profiles designer with drag-and-drop processor ordering. Enhanced tenant and API key management allow for guardrail profile assignment, cost ceilings, and environment tagging.

**System Design Choices:**

*   **Backend**: Python with FastAPI, SQLAlchemy ORM, organized into services for routing, guardrails, tenancy, usage, user, audit, billing, SSO, semantic caching, content routing, and stream inspection. Telemetry is integrated via OpenTelemetry.
*   **Database**: PostgreSQL is used for data persistence, managing tables for tenants, API keys, usage logs, users, audit logs, policies, provider configurations, and SSO configurations.
*   **Configuration**: Externalized configuration for models, providers, guardrails, and routing rules in YAML files.

### External Dependencies

*   **AI Providers**: OpenAI, Anthropic, Gemini (via LiteLLM)
*   **Guardrails**: NVIDIA NeMo Guardrails
*   **Database**: PostgreSQL
*   **Caching/State Management**: Redis (optional, for rate limiting, SSO state, and semantic cache)
*   **Authentication**: OIDC (for SSO)
*   **Monitoring/Telemetry**: OpenTelemetry (compatible with Datadog, Grafana, New Relic)
*   **Frontend Libraries**: React, Vite, Tailwind CSS
*   **Backend Libraries**: FastAPI, SQLAlchemy, LiteLLM, Uvicorn