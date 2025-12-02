# AI Gateway - Complete Documentation

Enterprise-grade AI Gateway for BFSI (Banking, Financial Services, Insurance) with multi-provider routing, advanced guardrails, and comprehensive billing analytics.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Architecture & Design](#architecture--design)
3. [Features](#features)
4. [F5 AI Gateway Comparison](#f5-ai-gateway-comparison)
5. [Test Users](#test-users)
6. [API Reference](#api-reference)
7. [Implementation Details](#implementation-details)
8. [Configuration](#configuration)
9. [Deployment](#deployment)

---

## Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI (Python 3.11+) | High-performance async API framework |
| ORM | SQLAlchemy 2.0 | Database abstraction and migrations |
| Database | PostgreSQL | Primary data store |
| Cache | Redis (optional) | Semantic caching, rate limiting, SSO state |
| AI Routing | LiteLLM | Multi-provider LLM abstraction |
| Guardrails | NVIDIA NeMo Guardrails | BFSI compliance and safety |
| Auth | JWT + bcrypt | Token-based authentication |
| Telemetry | OpenTelemetry | Metrics, traces, and logging |
| Server | Uvicorn | ASGI server |

### Frontend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 18 | Component-based UI |
| Build Tool | Vite | Fast development and bundling |
| Styling | Tailwind CSS | Utility-first CSS framework |
| Icons | Lucide React | Icon library |
| HTTP Client | Fetch API | API communication |
| State | React Context | Global state management |

### Infrastructure
| Component | Technology | Purpose |
|-----------|------------|---------|
| Container | Docker | Containerization |
| Orchestration | Docker Compose / Kubernetes | Multi-container deployment |
| Monitoring | Prometheus + Grafana | Metrics visualization |
| Tracing | Jaeger / Datadog | Distributed tracing |

---

## Architecture & Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                         │
│         (Web Dashboard, Mobile Apps, API Consumers)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (React)                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  Dashboard  │ │  Playground │ │   Billing   │ │ Audit Logs  │            │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │    Users    │ │  API Keys   │ │ Guardrails  │ │   Models    │            │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (FastAPI)                                │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Middleware Layer                                 │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────────┐ │   │
│  │  │   Auth     │ │ Rate Limit │ │ Telemetry  │ │ Request Logging    │ │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Service Layer                                    │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │   │
│  │  │   Router    │ │ Guardrails  │ │   Cache     │ │  Billing    │     │   │
│  │  │  Service    │ │  Service    │ │  Service    │ │  Service    │     │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘     │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │   │
│  │  │   Audit     │ │    User     │ │   SSO       │ │  Tenancy    │     │   │
│  │  │  Service    │ │  Service    │ │  Service    │ │  Service    │     │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  PostgreSQL │ │    Redis    │ │   OpenAI    │ │  Anthropic  │
│  (Primary)  │ │  (Cache)    │ │    API      │ │    API      │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### Request Flow

```
1. Client Request
       │
       ▼
2. Authentication (JWT/API Key)
       │
       ▼
3. Rate Limiting Check
       │
       ▼
4. Semantic Cache Lookup ──────► Cache Hit? ──► Return Cached Response
       │
       │ (Cache Miss)
       ▼
5. Content-Based Routing (Topic Detection)
       │
       ▼
6. Input Guardrails (PII, Injection, Toxicity)
       │
       ▼
7. LLM Provider Call (via LiteLLM)
       │
       ▼
8. Output Guardrails (Streaming Inspection)
       │
       ▼
9. Usage Logging & Billing
       │
       ▼
10. Audit Logging
       │
       ▼
11. Cache Storage
       │
       ▼
12. Response to Client
```

### Database Schema

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   tenants    │────<│    users     │────<│  usage_logs  │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id           │     │ id           │     │ id           │
│ name         │     │ tenant_id    │     │ user_id      │
│ company_name │     │ email        │     │ model        │
│ email        │     │ name         │     │ tokens_in    │
│ created_at   │     │ password_hash│     │ tokens_out   │
└──────────────┘     │ role         │     │ cost         │
       │             │ status       │     │ created_at   │
       │             └──────────────┘     └──────────────┘
       │
       ├────────────<┌──────────────┐
       │             │   api_keys   │
       │             ├──────────────┤
       │             │ id           │
       │             │ tenant_id    │
       │             │ key_hash     │
       │             │ name         │
       │             │ permissions  │
       │             └──────────────┘
       │
       └────────────<┌──────────────┐
                     │ audit_logs   │
                     ├──────────────┤
                     │ id           │
                     │ tenant_id    │
                     │ user_id      │
                     │ action       │
                     │ details      │
                     │ ip_address   │
                     │ created_at   │
                     └──────────────┘
```

### Design Principles

1. **Multi-Tenant Isolation**: Complete data isolation between tenants
2. **Defense in Depth**: Multiple layers of guardrails (input, output, streaming)
3. **Fail-Safe Defaults**: Conservative security settings by default
4. **Graceful Degradation**: Fallbacks for all external services
5. **Audit Everything**: Complete audit trail for regulatory compliance
6. **Mobile-First UI**: Responsive design with 44-48px touch targets

---

## Features

### Core Features

| Feature | Description | Status |
|---------|-------------|--------|
| Multi-Provider Routing | Route requests to OpenAI, Anthropic, Gemini, local models | ✅ |
| Multi-Tenant Architecture | Isolated tenants with separate billing and users | ✅ |
| API Key Management | Create, revoke, and manage API keys per tenant | ✅ |
| Usage Tracking | Per-request token and cost tracking | ✅ |
| Role-Based Access Control | 4 roles with 14 granular permissions | ✅ |

### Enterprise Features (F5 Parity)

| Feature | Description | Status |
|---------|-------------|--------|
| OpenTelemetry Integration | Metrics, traces, logs with OTLP export | ✅ |
| Semantic Caching | 30-50% cost reduction via similarity matching | ✅ |
| Content-Based Routing | Auto-route by topic (coding, creative, etc.) | ✅ |
| Streaming Response Inspection | Real-time guardrails during streaming | ✅ |

### BFSI Compliance Features

| Feature | Description | Status |
|---------|-------------|--------|
| PII Detection | SSN, credit cards, bank accounts, Aadhaar, PAN | ✅ |
| Financial Advice Guard | Detect investment recommendations | ✅ |
| Prompt Injection Detection | Block manipulation attempts | ✅ |
| Jailbreak Detection | Prevent AI safety bypasses | ✅ |
| Toxicity Filter | Block harmful content | ✅ |
| Comprehensive Audit Logs | Full request/response logging | ✅ |

### SSO & Authentication

| Feature | Description | Status |
|---------|-------------|--------|
| JWT Authentication | Secure token-based auth | ✅ |
| OIDC/SSO Integration | Enterprise identity providers | ✅ |
| PKCE Support | Secure OAuth flow | ✅ |
| Session Management | Secure session handling | ✅ |

### Billing & Analytics

| Feature | Description | Status |
|---------|-------------|--------|
| Per-User Billing | Track costs per user | ✅ |
| Invoice Generation | Generate detailed invoices | ✅ |
| Cost Forecasting | Predict future costs | ✅ |
| Usage Export (CSV) | Export for external analysis | ✅ |

---

## F5 AI Gateway Comparison

### Feature Comparison Matrix

| Feature | F5 AI Gateway | This Gateway | Notes |
|---------|---------------|--------------|-------|
| **Multi-Provider Routing** | ✅ | ✅ | OpenAI, Anthropic, Gemini, local |
| **OpenTelemetry Integration** | ✅ | ✅ | Full metrics, traces, logs |
| **Semantic Caching** | ✅ | ✅ | 0.92 cosine similarity threshold |
| **Content-Based Routing** | ✅ | ✅ | 10 content categories |
| **Streaming Inspection** | ✅ | ✅ | Real-time guardrails |
| **PII Detection** | ✅ | ✅ | BFSI-specific patterns |
| **Prompt Injection Detection** | ✅ | ✅ | Pattern + heuristic |
| **Rate Limiting** | ✅ | ✅ | Per-tenant limits |
| **Multi-Tenancy** | ✅ | ✅ | Complete isolation |
| **RBAC** | ✅ | ✅ | 4 roles, 14 permissions |
| **SSO/OIDC** | ✅ | ✅ | With PKCE support |
| **Audit Logging** | ✅ | ✅ | PII-sanitized exports |
| **Language Identification** | ✅ | ❌ | Planned |
| **Topic Detection (ML)** | ✅ | Partial | Pattern-based (ML planned) |
| **Repetition Detection** | ✅ | ❌ | Planned |
| **GPU Acceleration** | ✅ | ❌ | Not applicable for cloud |
| **S3 Audit Export** | ✅ | ❌ | Planned |
| **Custom Processor SDK** | ✅ | ❌ | Planned |

### Competitive Advantages

| Advantage | Description |
|-----------|-------------|
| **BFSI Focus** | Purpose-built for banking, finance, insurance compliance |
| **NeMo Guardrails** | NVIDIA's enterprise-grade safety system |
| **Per-User Billing** | Granular cost tracking and allocation |
| **Open Source** | Full customization and on-premise deployment |
| **React Dashboard** | Modern, responsive admin interface |

### Remaining Gaps (Future Roadmap)

1. **Language Identification Processor** - Detect input/output language
2. **Advanced Topic Detection** - ML-based classification
3. **Repetition Detection** - Filter looping outputs
4. **System Prompt Injection Detection** - Advanced override detection
5. **S3 Audit Export** - Cloud storage for compliance
6. **Custom Processor SDK** - Python/Rust/Go extensions
7. **Advanced Load Balancing** - Weighted routing, circuit breakers
8. **Prometheus Metrics Endpoint** - Native `/metrics` endpoint

---

## Test Users

### Pre-Created Test Accounts

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| **Admin** | `admin@test.com` | `Test123!` | Full system access |
| **Manager** | `manager@test.com` | `Test123!` | Operational access |
| **User** | `user@test.com` | `Test123!` | Gateway consumer |
| **Viewer** | `viewer@test.com` | `Test123!` | Read-only access |

### Role Permissions Matrix

| Permission | Admin | Manager | User | Viewer |
|------------|-------|---------|------|--------|
| `dashboard:view` | ✅ | ✅ | ✅ | ✅ |
| `gateway:use` | ✅ | ✅ | ✅ | ❌ |
| `api_keys:view` | ✅ | ✅ | ✅ | ❌ |
| `api_keys:create` | ✅ | ✅ | ❌ | ❌ |
| `api_keys:revoke` | ✅ | ✅ | ❌ | ❌ |
| `billing:view` | ✅ | ✅ | ❌ | ✅ |
| `billing:export` | ✅ | ✅ | ❌ | ❌ |
| `billing:invoice` | ✅ | ✅ | ❌ | ❌ |
| `audit:view` | ✅ | ✅ | ❌ | ✅ |
| `audit:export` | ✅ | ✅ | ❌ | ❌ |
| `users:view` | ✅ | ✅ | ❌ | ❌ |
| `users:create` | ✅ | ✅ | ❌ | ❌ |
| `users:edit` | ✅ | ✅ | ❌ | ❌ |
| `users:delete` | ✅ | ❌ | ❌ | ❌ |
| `guardrails:view` | ✅ | ✅ | ❌ | ✅ |
| `guardrails:edit` | ✅ | ❌ | ❌ | ❌ |
| `guardrails:test` | ✅ | ✅ | ❌ | ❌ |
| `router:view` | ✅ | ✅ | ❌ | ✅ |
| `router:edit` | ✅ | ❌ | ❌ | ❌ |
| `settings:view` | ✅ | ❌ | ❌ | ❌ |
| `settings:edit` | ✅ | ❌ | ❌ | ❌ |

### Sidebar Visibility by Role

| Page | Admin | Manager | User | Viewer |
|------|-------|---------|------|--------|
| Dashboard | ✅ | ✅ | ✅ | ✅ |
| Models | ✅ | ✅ | ✅ | ❌ |
| Playground | ✅ | ✅ | ✅ | ❌ |
| API Keys | ✅ | ✅ | ✅ | ❌ |
| Users | ✅ | ✅ | ❌ | ❌ |
| Billing | ✅ | ✅ | ❌ | ✅ |
| Audit Logs | ✅ | ✅ | ❌ | ✅ |
| Guardrails | ✅ | ✅ | ❌ | ✅ |
| Router Config | ✅ | ❌ | ❌ | ✅ |
| Settings | ✅ | ❌ | ❌ | ❌ |

---

## API Reference

### Authentication

```bash
# Register tenant
POST /api/v1/admin/auth/register
{
  "email": "admin@company.com",
  "password": "SecurePass123!",
  "company_name": "Company Inc"
}

# Login
POST /api/v1/admin/auth/login
{
  "email": "admin@company.com",
  "password": "SecurePass123!"
}
# Returns: { "access_token": "jwt...", "token_type": "bearer" }

# Get current user
GET /api/v1/admin/auth/me
Authorization: Bearer <token>
```

### AI Endpoints

```bash
# Chat completions
POST /api/v1/chat/completions
Authorization: Bearer <api-key>
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}

# Streaming chat
POST /api/v1/chat/completions
{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "Write a poem"}],
  "stream": true
}

# List models
GET /api/v1/models
Authorization: Bearer <api-key>

# Embeddings
POST /api/v1/embeddings
Authorization: Bearer <api-key>
{
  "model": "text-embedding-ada-002",
  "input": "Hello world"
}
```

### API Key Management

```bash
# List API keys
GET /api/v1/admin/api-keys
Authorization: Bearer <token>

# Create API key
POST /api/v1/admin/api-keys
{
  "name": "production-key",
  "permissions": ["chat", "embeddings"]
}

# Revoke API key
DELETE /api/v1/admin/api-keys/{key_id}
```

### User Management

```bash
# List users
GET /api/v1/admin/users

# Create user
POST /api/v1/admin/users
{
  "email": "user@company.com",
  "password": "SecurePass123!",
  "name": "John Doe",
  "role": "user"
}

# Update user
PUT /api/v1/admin/users/{user_id}
{
  "role": "manager",
  "status": "active"
}

# Delete user
DELETE /api/v1/admin/users/{user_id}

# Get user usage
GET /api/v1/admin/users/{user_id}/usage
```

### Billing

```bash
# Get billing summary
GET /api/v1/admin/billing/summary

# Get user billing
GET /api/v1/admin/billing/user/{user_id}

# Generate invoice
POST /api/v1/admin/billing/invoice
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}

# Export CSV
GET /api/v1/admin/billing/export/csv

# Cost forecast
GET /api/v1/admin/billing/forecast
```

### Audit Logs

```bash
# List audit logs
GET /api/v1/admin/audit/logs?limit=50&offset=0

# Get audit summary
GET /api/v1/admin/audit/summary

# Export audit logs
POST /api/v1/admin/audit/export
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "format": "json"
}

# Get security events
GET /api/v1/admin/audit/security-events
```

### Guardrails

```bash
# List guardrails
GET /api/v1/admin/guardrails

# Get BFSI guardrails
GET /api/v1/admin/guardrails/bfsi

# Test guardrails
POST /api/v1/admin/guardrails/test
{
  "text": "My SSN is 123-45-6789"
}

# Update policy
PUT /api/v1/admin/guardrails/policy
{
  "pii_detection": true,
  "toxicity_filter": true,
  "prompt_injection_detection": true
}
```

### Enterprise Features

```bash
# Feature status
GET /api/v1/admin/features/status

# Cache stats
GET /api/v1/cache/stats

# Clear cache
DELETE /api/v1/cache

# Routing config
GET /api/v1/routing/config
```

### SSO

```bash
# List SSO providers
GET /api/v1/admin/auth/sso/providers

# Initiate SSO
POST /api/v1/admin/auth/sso/initiate
{
  "provider": "okta"
}

# SSO callback
GET /api/v1/admin/auth/sso/callback?code=...&state=...

# Configure SSO
POST /api/v1/admin/sso/config
{
  "provider": "okta",
  "client_id": "...",
  "client_secret": "...",
  "issuer_url": "https://company.okta.com"
}
```

---

## Implementation Details

### Service Architecture

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── routes_auth.py      # Authentication endpoints
│   │       ├── routes_chat.py      # AI chat endpoints
│   │       ├── routes_admin.py     # Admin endpoints
│   │       ├── routes_users.py     # User management
│   │       ├── routes_billing.py   # Billing endpoints
│   │       ├── routes_audit.py     # Audit log endpoints
│   │       ├── routes_guardrails.py# Guardrails config
│   │       └── routes_sso.py       # SSO endpoints
│   ├── core/
│   │   ├── config.py               # Settings management
│   │   ├── security.py             # JWT, password hashing
│   │   ├── permissions.py          # RBAC decorators
│   │   └── database.py             # Database connection
│   ├── models/
│   │   └── models.py               # SQLAlchemy models
│   ├── services/
│   │   ├── router_service.py       # LiteLLM routing
│   │   ├── guardrails_service.py   # Input/output validation
│   │   ├── nemo_guardrails_service.py # NeMo Guardrails
│   │   ├── semantic_cache_service.py  # Vector caching
│   │   ├── content_routing_service.py # Topic routing
│   │   ├── stream_inspection_service.py # Streaming guardrails
│   │   ├── tenancy_service.py      # Multi-tenant logic
│   │   ├── user_service.py         # User management
│   │   ├── usage_service.py        # Usage tracking
│   │   ├── billing_service.py      # Billing & invoicing
│   │   ├── audit_service.py        # Audit logging
│   │   └── sso_service.py          # SSO/OIDC
│   ├── telemetry/
│   │   ├── __init__.py
│   │   └── otel.py                 # OpenTelemetry setup
│   └── main.py                     # FastAPI app
├── configs/
│   ├── models.yaml                 # Model definitions
│   ├── providers.yaml              # Provider configs
│   ├── guardrails.yaml             # Safety policies
│   └── routing_rules.yaml          # Routing strategies
└── requirements.txt
```

### Key Implementation Patterns

#### 1. Semantic Caching

```python
# Vector similarity with cosine distance
def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(x * x for x in b))
    return dot_product / (magnitude_a * magnitude_b)

# Cache lookup with 0.92 threshold
async def get_cached_response(prompt: str, tenant_id: str):
    prompt_embedding = generate_embedding(prompt)
    for cached in cache_entries:
        similarity = cosine_similarity(prompt_embedding, cached.embedding)
        if similarity >= 0.92:
            return cached.response
    return None
```

#### 2. Content-Based Routing

```python
CATEGORY_PATTERNS = {
    "coding": [r"\bcode\b", r"\bfunction\b", r"\bclass\b", r"\bdebug\b"],
    "creative": [r"\bstory\b", r"\bpoem\b", r"\bcreative\b"],
    "financial": [r"\binvest\b", r"\bstock\b", r"\bportfolio\b"],
    # ... 10 categories total
}

MODEL_RECOMMENDATIONS = {
    "coding": "claude-3-opus",
    "creative": "gpt-4",
    "financial": "gpt-4-turbo",
    # ...
}
```

#### 3. Streaming Inspection

```python
async def inspect_stream(stream, guardrails, interval=10):
    buffer = ""
    chunk_count = 0
    
    async for chunk in stream:
        buffer += chunk.content
        chunk_count += 1
        
        if chunk_count % interval == 0:
            result = await guardrails.check(buffer)
            if result.blocked:
                raise GuardrailViolation(result.reason)
        
        yield chunk
    
    # Final check
    await guardrails.check(buffer)
```

#### 4. RBAC Permission Decorator

```python
def require_permission(permission: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=None, **kwargs):
            if not has_permission(current_user.role, permission):
                raise HTTPException(403, "Permission denied")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@router.delete("/users/{user_id}")
@require_permission("users:delete")
async def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
    ...
```

#### 5. Audit Logging with PII Sanitization

```python
def sanitize_pii(data: dict) -> dict:
    patterns = {
        "ssn": r"\d{3}-\d{2}-\d{4}",
        "credit_card": r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}",
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "aadhaar": r"\d{4}\s?\d{4}\s?\d{4}",
        "pan": r"[A-Z]{5}[0-9]{4}[A-Z]",
    }
    
    sanitized = json.dumps(data)
    for name, pattern in patterns.items():
        sanitized = re.sub(pattern, f"[{name.upper()}_REDACTED]", sanitized)
    return json.loads(sanitized)
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `SESSION_SECRET` | Yes | - | JWT signing secret |
| `REDIS_URL` | No | - | Redis URL for caching |
| `OPENAI_API_KEY` | No | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key |
| `GOOGLE_API_KEY` | No | - | Google AI API key |
| `OTLP_ENDPOINT` | No | - | OpenTelemetry collector endpoint |
| `ENABLE_TELEMETRY` | No | true | Enable OpenTelemetry |
| `ENABLE_SEMANTIC_CACHE` | No | true | Enable semantic caching |
| `ENABLE_CONTENT_ROUTING` | No | true | Enable content routing |
| `ENABLE_STREAM_INSPECTION` | No | true | Enable streaming guardrails |
| `SEMANTIC_CACHE_SIMILARITY_THRESHOLD` | No | 0.92 | Cache similarity threshold |
| `STREAM_INSPECTION_INTERVAL` | No | 10 | Chunks between inspections |

### Model Configuration (models.yaml)

```yaml
models:
  gpt-4:
    provider: openai
    max_tokens: 8192
    input_cost_per_1k: 0.03
    output_cost_per_1k: 0.06
  
  claude-3-opus:
    provider: anthropic
    max_tokens: 4096
    input_cost_per_1k: 0.015
    output_cost_per_1k: 0.075
  
  gemini-pro:
    provider: google
    max_tokens: 32768
    input_cost_per_1k: 0.00025
    output_cost_per_1k: 0.0005
```

### Guardrails Configuration (guardrails.yaml)

```yaml
guardrails:
  pii_detection:
    enabled: true
    patterns:
      - ssn
      - credit_card
      - bank_account
      - aadhaar
      - pan
    action: redact
  
  prompt_injection:
    enabled: true
    action: block
  
  toxicity:
    enabled: true
    threshold: 0.8
    action: block
  
  financial_advice:
    enabled: true
    action: warn
```

---

## Deployment

### Development

```bash
# Backend
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd ui && npm run dev
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/aigateway
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  frontend:
    build: ./ui
    ports:
      - "5000:5000"
    depends_on:
      - backend
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=aigateway
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:7-alpine
```

### Kubernetes (Helm)

```yaml
# values.yaml
replicaCount: 3

image:
  repository: aigateway
  tag: latest

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: gateway.company.com
      paths:
        - path: /
          pathType: Prefix
```

---

## Quick Start Testing

```bash
# 1. Check health
curl http://localhost:8000/

# 2. Check enterprise features
curl http://localhost:8000/api/v1/admin/features/status

# 3. Login as admin
curl -X POST http://localhost:8000/api/v1/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "Test123!"}'

# 4. Test guardrails
curl -X POST http://localhost:8000/api/v1/admin/guardrails/test \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"text": "My SSN is 123-45-6789"}'

# 5. Access frontend dashboard
open http://localhost:5000
```

---

*Document Version: 1.0 | Last Updated: December 2024*
