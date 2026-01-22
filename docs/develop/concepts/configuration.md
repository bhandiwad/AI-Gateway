# Configuration

Complete reference for AI Gateway configuration options.

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET_KEY` | Secret for JWT signing (32+ chars) |

### AI Providers

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `GOOGLE_API_KEY` | Google AI API key |
| `XAI_API_KEY` | xAI (Grok) API key |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_TELEMETRY` | `false` | Enable OpenTelemetry |
| `ENABLE_SEMANTIC_CACHE` | `false` | Enable response caching |
| `DEBUG` | `false` | Enable debug mode |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT expiration |

---

## Example .env

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_gateway

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET_KEY=your-secret-key-minimum-32-characters

# Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Features
ENABLE_TELEMETRY=false
ENABLE_SEMANTIC_CACHE=true

# Application
DEBUG=false
LOG_LEVEL=INFO
```

---

## Configuration Hierarchy

1. Environment variables (highest priority)
2. `.env` file
3. Default values

---

## See Also

- [Deployment Guide](../../deploy/index.md)
- [Docker Configuration](../../deploy/docker.md)
