# AI Gateway

**Enterprise-grade AI Gateway with multi-provider routing, guardrails, and usage tracking.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal?logo=fastapi)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Documentation

**[Read the full documentation →](docs/index.md)**

| Section | Description |
|---------|-------------|
| [**Get Started**](docs/get-started/index.md) | Installation, quickstart, and main concepts |
| [**Develop**](docs/develop/index.md) | API reference, tutorials, and integrations |
| [**Deploy**](docs/deploy/index.md) | Docker, Kubernetes, and cloud deployment |
| [**Knowledge Base**](docs/knowledge-base/index.md) | FAQ, troubleshooting, and tips |

---

## Quick Start

```bash
# Clone and configure
git clone https://github.com/your-org/ai-gateway.git
cd ai-gateway
cp .env.example .env

# Start services
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

**That's it!**

- **Dashboard**: http://localhost
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

---

## First API Call

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/admin/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email": "test@example.com", "password": "Password123!"}'

# 2. Create API key (use token from step 1)
curl -X POST http://localhost:8000/api/v1/admin/api-keys \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "My Key"}'

# 3. Chat completion
curl http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hello!"}]}'
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI Gateway                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   React UI  │  │  FastAPI    │  │  PostgreSQL │              │
│  │  Dashboard  │◄─┤   Backend   │◄─┤   Database  │              │
│  └─────────────┘  └──────┬──────┘  └─────────────┘              │
│                          │                                       │
│  ┌───────────────────────┼───────────────────────┐              │
│  │              Middleware Stack                  │              │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐         │              │
│  │  │Auth/RBAC│ │Guardrails│ │Rate Limit│        │              │
│  │  └─────────┘ └─────────┘ └─────────┘         │              │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐         │              │
│  │  │ Logging │ │ Caching │ │ Metrics │         │              │
│  │  └─────────┘ └─────────┘ └─────────┘         │              │
│  └───────────────────────┼───────────────────────┘              │
│                          │                                       │
│  ┌───────────────────────┼───────────────────────┐              │
│  │            Router & Load Balancer              │              │
│  │  ┌─────────────────────────────────────────┐  │              │
│  │  │  Circuit Breaker │ Fallback │ Retry     │  │              │
│  │  └─────────────────────────────────────────┘  │              │
│  └───────────────────────┼───────────────────────┘              │
│                          │                                       │
├──────────────────────────┼──────────────────────────────────────┤
│                    AI Providers                                  │
│  ┌────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐ ┌─────────────┐│
│  │ OpenAI │ │ Anthropic│ │ Google │ │  Azure  │ │ Local vLLM  ││
│  └────────┘ └──────────┘ └────────┘ └─────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/ARCHITECTURE.md) | System design and components |
| [Configuration](docs/CONFIGURATION.md) | Environment variables and settings |
| [Deployment](docs/DEPLOYMENT.md) | Production deployment guide |
| [API Reference](docs/API.md) | Complete API documentation |
| [Guardrails](docs/GUARDRAILS.md) | Security guardrails configuration |
| [File Guardrails](docs/FILE_GUARDRAILS.md) | Apply guardrails to uploaded files |
| [Statistics](docs/STATISTICS.md) | Usage analytics and reporting |
| [Prompt Caching](docs/PROMPT_CACHING.md) | Semantic caching for cost savings |
| [SSO Setup](docs/SSO.md) | Single Sign-On integration |

---

## Key Features

### Enterprise Guardrails
- **PII Detection & Redaction** - Email, phone, SSN, Aadhaar, PAN, credit cards
- **Compliance Processors** - DPDP, GDPR, HIPAA, PCI-DSS compliance checks
- **Prompt Injection Detection** - Block malicious prompt manipulation
- **Secrets Detection** - Prevent API keys, tokens from leaking
- **File Content Scanning** - Apply guardrails to uploaded PDFs, DOCX, images (OCR)

### Statistics & Analytics
- **Comprehensive Dashboard** - Requests, tokens, costs (₹ INR)
- **Per-User/Department Analytics** - Track usage by user, team, department
- **API Key Metrics** - Hits, success rates per API key
- **Model Usage** - Top models, provider breakdown
- **Hourly Distribution** - Request patterns over time

### Prompt Caching
- **Semantic Cache** - Reuse responses for similar prompts (92% similarity)
- **Token Savings Tracking** - See how many tokens saved
- **Cost Savings** - Track money saved from cache hits
- **Cache Management** - View stats, clear cache via UI

### Intelligent Routing
- **Multi-Provider Support** - OpenAI, Anthropic, Google, Azure, AWS Bedrock
- **Load Balancing** - Round-robin, weighted, least-latency
- **Circuit Breaker** - Automatic failover on provider errors
- **Budget Enforcement** - Per-user, per-department spending limits

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `JWT_SECRET_KEY` | Secret for JWT tokens | (required) |
| `OPENAI_API_KEY` | OpenAI API key | (optional) |
| `ANTHROPIC_API_KEY` | Anthropic API key | (optional) |
| `ENABLE_TELEMETRY` | Enable OpenTelemetry | `false` |
| `ENABLE_SEMANTIC_CACHE` | Enable semantic caching | `false` |

See [Configuration Guide](docs/CONFIGURATION.md) for complete reference.

---

## API Reference

### Authentication

```bash
# Register
POST /api/v1/admin/auth/register
{
  "name": "Your Name",
  "email": "you@example.com",
  "password": "SecurePassword123!"
}

# Login
POST /api/v1/admin/auth/login
{
  "email": "you@example.com",
  "password": "SecurePassword123!"
}
```

### Chat Completions (OpenAI-compatible)

```bash
POST /api/v1/chat/completions
Authorization: Bearer YOUR_API_KEY

{
  "model": "gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

### API Key Management

```bash
# Create API Key
POST /api/v1/admin/api-keys
Authorization: Bearer YOUR_JWT_TOKEN
{
  "name": "Production Key",
  "environment": "production"
}

# List API Keys
GET /api/v1/admin/api-keys

# Revoke API Key
DELETE /api/v1/admin/api-keys/{key_id}
```

### Guardrails

```bash
# Test Guardrails
POST /api/v1/admin/guardrails/test
{
  "text": "Test content with PII: 123-45-6789",
  "policy": "default",
  "is_input": true
}
```

Full API documentation available at `/docs` (Swagger UI) or `/redoc` (ReDoc).

---

## Testing

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run tests in parallel
pytest -n auto
```

### Test Categories

| Test File | Coverage |
|-----------|----------|
| `test_auth.py` | Authentication, registration, login, SSO |
| `test_api_keys.py` | API key CRUD, authentication |
| `test_chat_completions.py` | Chat API, streaming, parameters |
| `test_guardrails.py` | PII detection, prompt injection, policies |
| `test_router.py` | Routing, providers, load balancing |
| `test_tenants.py` | Tenant management, settings |
| `test_users.py` | User CRUD, permissions |
| `test_billing.py` | Usage tracking, budgets |
| `test_audit.py` | Audit logging |

---

## Deployment

### Docker Compose (Development/Staging)

```bash
docker-compose up -d
```

### Kubernetes (Production)

```bash
# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods -n ai-gateway
```

### Cloud Platforms

- **AWS**: See [AWS Deployment Guide](docs/deployment/AWS.md)
- **GCP**: See [GCP Deployment Guide](docs/deployment/GCP.md)
- **Azure**: See [Azure Deployment Guide](docs/deployment/AZURE.md)

---

## Security

### Reporting Vulnerabilities

Please report security vulnerabilities to security@your-org.com. Do not create public issues for security concerns.

### Security Features

- All passwords hashed with bcrypt
- JWT tokens with configurable expiration
- Rate limiting per tenant/API key
- PII redaction in logs
- HTTPS enforced in production
- CORS configuration
- Input validation on all endpoints

---

## Monitoring

### Health Checks

```bash
# Basic health
GET /health

# Detailed metrics
GET /metrics

# Feature status
GET /api/v1/admin/features/status
```

### Observability

- **Metrics**: Prometheus-compatible `/metrics` endpoint
- **Tracing**: OpenTelemetry integration
- **Logging**: Structured JSON logs with request correlation

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for frontend development
- Write tests for new features
- Update documentation as needed

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - Frontend library
- [OpenAI](https://openai.com/) - API design inspiration
- [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) - Guardrails framework

---

<div align="center">
Made by the AI Gateway Team
</div>
