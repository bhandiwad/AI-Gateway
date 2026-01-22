# 🏗️ AI Gateway Architecture

## Overview

AI Gateway is built as a modern, scalable microservices-inspired monolith using Python FastAPI for the backend and React for the frontend. This document describes the system architecture, key components, and design decisions.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Web UI    │  │   CLI       │  │   SDK       │  │   Direct    │        │
│  │  (React)    │  │   Tools     │  │   Clients   │  │   API       │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API Gateway Layer                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         FastAPI Application                          │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐           │   │
│  │  │   Auth    │ │   Rate    │ │  Request  │ │  Logging  │           │   │
│  │  │Middleware │ │  Limiter  │ │ Validator │ │Middleware │           │   │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Service Layer                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Router    │  │  Guardrail  │  │   Tenancy   │  │    User     │        │
│  │   Service   │  │   Service   │  │   Service   │  │   Service   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    SSO      │  │   Billing   │  │   Audit     │  │   Cache     │        │
│  │   Service   │  │   Service   │  │   Service   │  │   Service   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Infrastructure Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │ PostgreSQL  │  │    Redis    │  │   Object    │                         │
│  │  Database   │  │    Cache    │  │   Storage   │                         │
│  └─────────────┘  └─────────────┘  └─────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Provider Layer                                       │
│  ┌────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐ ┌──────┐ ┌─────────────┐  │
│  │ OpenAI │ │ Anthropic│ │ Google │ │  Azure  │ │  xAI │ │ Local vLLM  │  │
│  └────────┘ └──────────┘ └────────┘ └─────────┘ └──────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. API Layer (`backend/app/api/`)

The API layer handles HTTP requests and routes them to appropriate services.

```
api/
├── v1/
│   ├── routes_admin.py      # Admin endpoints (auth, tenants, keys)
│   ├── routes_chat.py       # Chat completions (OpenAI-compatible)
│   ├── routes_users.py      # User management
│   ├── routes_guardrails.py # Guardrail configuration
│   ├── routes_router.py     # Routing configuration
│   ├── routes_billing.py    # Usage and billing
│   ├── routes_audit.py      # Audit logs
│   └── routes_alerts.py     # Alert management
```

**Key Design Decisions:**
- OpenAI-compatible API for easy migration
- Versioned API (`/api/v1/`) for backward compatibility
- Separate admin and user-facing endpoints
- Dependency injection for services

### 2. Service Layer (`backend/app/services/`)

Business logic is encapsulated in service classes.

```
services/
├── router_service.py        # AI provider routing logic
├── guardrail_service.py     # Guardrail processing
├── tenancy_service.py       # Tenant management
├── user_service.py          # User operations
├── sso_service.py           # SSO/OIDC integration
├── billing_service.py       # Cost tracking
├── audit_service.py         # Audit logging
├── load_balancer.py         # Request distribution
├── circuit_breaker.py       # Failure handling
└── semantic_cache_service.py # Response caching
```

### 3. Data Layer (`backend/app/db/`)

SQLAlchemy ORM models and database session management.

```
db/
├── models/
│   ├── tenant.py            # Tenant/organization model
│   ├── user.py              # User model
│   ├── api_key.py           # API key model
│   ├── usage_log.py         # Usage tracking
│   ├── audit_log.py         # Audit entries
│   ├── sso_config.py        # SSO provider config
│   └── provider_config.py   # AI provider settings
├── session.py               # Database session factory
└── migrations/              # SQL migrations
```

### 4. Core (`backend/app/core/`)

Cross-cutting concerns and utilities.

```
core/
├── config.py                # Application settings
├── security.py              # JWT, password hashing
├── rate_limit.py            # Rate limiting logic
├── permissions.py           # RBAC definitions
└── api_key_cache.py         # API key validation cache
```

---

## Request Flow

### Chat Completion Request

```
1. Request arrives at /api/v1/chat/completions
                    │
                    ▼
2. Authentication Middleware
   - Validates JWT token or API key
   - Extracts tenant/user context
                    │
                    ▼
3. Rate Limit Check
   - Per-tenant rate limiting
   - Per-API-key rate limiting
                    │
                    ▼
4. Guardrail Processing (Input)
   - PII detection/redaction
   - Prompt injection detection
   - Content policy check
                    │
                    ▼
5. Router Service
   - Select provider based on strategy
   - Check provider health
   - Apply load balancing
                    │
                    ▼
6. Provider Request
   - Transform to provider format
   - Send request with circuit breaker
   - Handle retries/failover
                    │
                    ▼
7. Guardrail Processing (Output)
   - PII detection in response
   - Content moderation
                    │
                    ▼
8. Usage Logging
   - Record tokens, cost
   - Update tenant spend
                    │
                    ▼
9. Return Response
   - OpenAI-compatible format
   - Include usage metadata
```

---

## Database Schema

### Core Tables

```sql
-- Tenants (Organizations)
tenants
├── id (PK)
├── name
├── email
├── password_hash
├── is_active
├── is_admin
├── rate_limit
├── monthly_budget
├── current_spend
├── allowed_models (JSON)
├── allowed_providers (JSON)
├── logging_policy (JSON)
├── created_at
└── updated_at

-- Users (within tenants)
users
├── id (PK)
├── tenant_id (FK)
├── email
├── name
├── role
├── is_active
└── created_at

-- API Keys
api_keys
├── id (PK)
├── tenant_id (FK)
├── name
├── key_hash
├── key_prefix
├── is_active
├── environment
├── rate_limit_override
├── allowed_models_override (JSON)
├── expires_at
└── created_at

-- Usage Logs
usage_logs
├── id (PK)
├── tenant_id (FK)
├── api_key_id (FK)
├── user_id (FK)
├── model
├── provider
├── prompt_tokens
├── completion_tokens
├── cost
├── latency_ms
├── status
└── created_at
```

---

## Security Architecture

### Authentication Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API Gateway │────▶│   Service   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              ┌─────┴─────┐ ┌─────┴─────┐
              │ JWT Token │ │  API Key  │
              └─────┬─────┘ └─────┬─────┘
                    │             │
              ┌─────┴─────┐ ┌─────┴─────┐
              │  Decode   │ │  Lookup   │
              │  Verify   │ │  Cache    │
              └─────┬─────┘ └─────┬─────┘
                    │             │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │   Extract   │
                    │   Context   │
                    └─────────────┘
```

### Permission Model

```python
class Permission(Enum):
    # Gateway permissions
    GATEWAY_USE = "gateway:use"
    
    # API Key permissions
    API_KEYS_VIEW = "api_keys:view"
    API_KEYS_CREATE = "api_keys:create"
    API_KEYS_DELETE = "api_keys:delete"
    
    # User permissions
    USERS_VIEW = "users:view"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DELETE = "users:delete"
    
    # Admin permissions
    TENANTS_VIEW = "tenants:view"
    TENANTS_UPDATE = "tenants:update"
    GUARDRAILS_TEST = "guardrails:test"
```

---

## Caching Strategy

### Multi-Level Cache

```
┌─────────────────────────────────────────────────────┐
│                   Request                            │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              L1: API Key Cache                       │
│         (In-memory, <1ms lookup)                    │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│           L2: Semantic Response Cache                │
│      (Redis, similarity-based matching)             │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              L3: Provider Response                   │
│              (Actual API call)                       │
└─────────────────────────────────────────────────────┘
```

---

## Scalability Considerations

### Horizontal Scaling

- **Stateless API servers**: Scale FastAPI instances behind load balancer
- **Shared Redis**: Session and cache data accessible across instances
- **Database connection pooling**: Efficient PostgreSQL connections

### Performance Optimizations

1. **API Key Caching**: Avoid database lookups on every request
2. **Async I/O**: Non-blocking provider calls
3. **Connection Pooling**: Reuse HTTP connections to providers
4. **Semantic Caching**: Reduce redundant API calls

---

## Monitoring & Observability

### Metrics

- Request count, latency, error rate
- Token usage by model/provider
- Cache hit/miss rates
- Circuit breaker states

### Tracing

- OpenTelemetry integration
- Request correlation IDs
- Distributed tracing across services

### Logging

- Structured JSON logs
- Request/response logging (with PII redaction)
- Audit trail for compliance

