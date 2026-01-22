# ⚙️ Configuration Reference

This document provides a comprehensive reference for all configuration options in AI Gateway.

---

## Environment Variables

### Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `DB_POOL_SIZE` | Connection pool size | `10` | No |
| `DB_MAX_OVERFLOW` | Max overflow connections | `20` | No |
| `DB_POOL_TIMEOUT` | Pool timeout (seconds) | `30` | No |

**Example:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/ai_gateway
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

### Redis Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` | Yes |
| `REDIS_PASSWORD` | Redis password | - | No |
| `REDIS_DB` | Redis database number | `0` | No |

**Example:**
```env
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your-redis-password
```

### Security Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `JWT_SECRET_KEY` | Secret key for JWT signing | - | Yes |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `1440` (24h) | No |
| `BCRYPT_ROUNDS` | Password hashing rounds | `12` | No |

**Example:**
```env
JWT_SECRET_KEY=your-super-secret-key-at-least-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### AI Provider API Keys

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | No* |
| `ANTHROPIC_API_KEY` | Anthropic API key | - | No* |
| `GOOGLE_API_KEY` | Google AI API key | - | No |
| `XAI_API_KEY` | xAI (Grok) API key | - | No |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key | - | No |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint | - | No |
| `AWS_ACCESS_KEY_ID` | AWS access key for Bedrock | - | No |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - | No |
| `AWS_REGION` | AWS region | `us-east-1` | No |

*At least one provider must be configured.

**Example:**
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
```

### Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_TELEMETRY` | Enable OpenTelemetry | `false` |
| `ENABLE_SEMANTIC_CACHE` | Enable semantic caching | `false` |
| `ENABLE_CONTENT_ROUTING` | Enable content-based routing | `false` |
| `ENABLE_STREAM_INSPECTION` | Enable stream content inspection | `false` |

**Example:**
```env
ENABLE_TELEMETRY=true
ENABLE_SEMANTIC_CACHE=true
ENABLE_CONTENT_ROUTING=false
```

### Telemetry Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OTLP_ENDPOINT` | OpenTelemetry collector endpoint | - |
| `TELEMETRY_CONSOLE_EXPORT` | Export traces to console | `false` |
| `SERVICE_NAME` | Service name for tracing | `ai-gateway` |

**Example:**
```env
ENABLE_TELEMETRY=true
OTLP_ENDPOINT=http://jaeger:4317
SERVICE_NAME=ai-gateway-prod
```

### Semantic Cache Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SEMANTIC_CACHE_SIMILARITY_THRESHOLD` | Similarity threshold (0-1) | `0.95` |
| `SEMANTIC_CACHE_TTL_SECONDS` | Cache TTL | `3600` |
| `SEMANTIC_CACHE_MAX_SIZE` | Maximum cache entries | `10000` |

**Example:**
```env
ENABLE_SEMANTIC_CACHE=true
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.92
SEMANTIC_CACHE_TTL_SECONDS=7200
```

### Stream Inspection Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `STREAM_INSPECTION_INTERVAL` | Inspection interval (chars) | `100` |
| `STREAM_INSPECTION_MIN_CHARS` | Minimum chars before inspection | `50` |

### Rate Limiting

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_RATE_LIMIT_RPM` | Default requests per minute | `100` |
| `DEFAULT_RATE_LIMIT_TPM` | Default tokens per minute | `100000` |
| `RATE_LIMIT_BURST_MULTIPLIER` | Burst allowance multiplier | `1.5` |

### Application Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `PROJECT_NAME` | Application name | `AI Gateway` |
| `VERSION` | Application version | `1.0.0` |
| `DEBUG` | Debug mode | `false` |
| `API_V1_PREFIX` | API version prefix | `/api/v1` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (json/text) | `json` |

---

## Configuration Files

### `.env` File

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_gateway

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-secret-key-minimum-32-characters-long

# AI Providers
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Features
ENABLE_TELEMETRY=false
ENABLE_SEMANTIC_CACHE=false

# Application
DEBUG=false
LOG_LEVEL=INFO
```

### Docker Compose Override

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'

services:
  backend:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    volumes:
      - ./backend:/app/backend:ro
    
  frontend:
    volumes:
      - ./ui/src:/app/src:ro
```

---

## Provider Configuration

### OpenAI

```env
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...  # Optional
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional, for proxies
```

### Anthropic

```env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_BASE_URL=https://api.anthropic.com  # Optional
```

### Azure OpenAI

```env
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

### Google AI (Gemini)

```env
GOOGLE_API_KEY=AIza...
GOOGLE_PROJECT_ID=your-project-id  # For Vertex AI
GOOGLE_LOCATION=us-central1  # For Vertex AI
```

### AWS Bedrock

```env
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
AWS_BEDROCK_RUNTIME_ENDPOINT=  # Optional custom endpoint
```

### Local vLLM

```env
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=  # Optional if auth enabled
```

---

## Guardrail Configuration

### Default Policies

Guardrails can be configured via the admin API or database. Default policies include:

| Policy | Description |
|--------|-------------|
| `default` | Standard protection (PII detection, basic injection) |
| `strict` | Enhanced protection (block on any detection) |
| `permissive` | Minimal filtering (logging only) |
| `bfsi` | Banking/Financial services compliance |

### PII Detection Settings

Configure via environment or API:

```env
GUARDRAIL_PII_ENABLED=true
GUARDRAIL_PII_TYPES=ssn,credit_card,email,phone,address
GUARDRAIL_PII_ACTION=redact  # redact, block, or warn
```

### Prompt Injection Detection

```env
GUARDRAIL_INJECTION_ENABLED=true
GUARDRAIL_INJECTION_ACTION=block
GUARDRAIL_INJECTION_SENSITIVITY=medium  # low, medium, high
```

---

## Logging Configuration

### Structured Logging

```env
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_INCLUDE_TIMESTAMP=true
LOG_INCLUDE_REQUEST_ID=true
```

### Log Output

```env
LOG_OUTPUT=stdout  # stdout, file, both
LOG_FILE_PATH=/var/log/ai-gateway/app.log
LOG_FILE_MAX_SIZE=100MB
LOG_FILE_BACKUP_COUNT=5
```

### PII Redaction in Logs

```env
LOG_REDACT_PII=true
LOG_REDACT_API_KEYS=true
LOG_REDACT_PASSWORDS=true
```

---

## Performance Tuning

### Connection Pool Settings

```env
# Database
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# HTTP Client
HTTP_CLIENT_TIMEOUT=120
HTTP_CLIENT_MAX_CONNECTIONS=100
HTTP_CLIENT_MAX_KEEPALIVE=20
```

### Caching

```env
# API Key Cache
API_KEY_CACHE_TTL=300
API_KEY_CACHE_MAX_SIZE=10000

# Response Cache
SEMANTIC_CACHE_ENABLED=true
SEMANTIC_CACHE_TTL=3600
SEMANTIC_CACHE_MAX_SIZE=10000
```

### Worker Configuration

For production with Gunicorn:

```env
WORKERS=4  # Usually 2-4 x CPU cores
WORKER_CLASS=uvicorn.workers.UvicornWorker
WORKER_TIMEOUT=120
KEEPALIVE=5
```

---

## Security Hardening

### Production Security

```env
# Disable debug
DEBUG=false

# Strict CORS
CORS_ORIGINS=https://your-domain.com
CORS_ALLOW_CREDENTIALS=true

# Session security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=strict

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=redis
```

### API Key Security

```env
# Key generation
API_KEY_PREFIX=sk-gw-
API_KEY_LENGTH=48
API_KEY_HASH_ALGORITHM=sha256

# Key policies
API_KEY_MAX_AGE_DAYS=365
API_KEY_REQUIRE_EXPIRY=false
```

---

## Example Complete Configuration

### Development (.env.development)

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_gateway_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=dev-secret-key-not-for-production-use
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Providers
OPENAI_API_KEY=sk-...

# Features
ENABLE_TELEMETRY=false
ENABLE_SEMANTIC_CACHE=false

# Debug
DEBUG=true
LOG_LEVEL=DEBUG
LOG_FORMAT=text
```

### Production (.env.production)

```env
# Database
DATABASE_URL=postgresql://user:${DB_PASSWORD}@db.internal:5432/ai_gateway
DB_POOL_SIZE=30
DB_MAX_OVERFLOW=50

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@redis.internal:6379/0

# Security
JWT_SECRET_KEY=${JWT_SECRET}
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Providers
OPENAI_API_KEY=${OPENAI_API_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# Features
ENABLE_TELEMETRY=true
OTLP_ENDPOINT=http://otel-collector:4317
ENABLE_SEMANTIC_CACHE=true

# Production settings
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json
CORS_ORIGINS=https://gateway.yourcompany.com
```

