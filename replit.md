# AI Gateway

Enterprise-grade AI Gateway with multi-provider routing, guardrails, and usage analytics.

## Overview

This is a full-stack AI Gateway application that provides:
- Unified API for multiple AI providers (OpenAI, Anthropic, etc.)
- Multi-tenant architecture with API key management
- Input/output guardrails for safety and compliance
- Usage tracking and cost analytics
- React-based admin dashboard

## Architecture

### Backend (Python/FastAPI)
- **Location**: `backend/`
- **Framework**: FastAPI with SQLAlchemy ORM
- **Key Services**:
  - `router_service.py`: LiteLLM-based multi-provider routing
  - `guardrails_service.py`: Input/output validation (PII, toxicity, prompt injection)
  - `tenancy_service.py`: Multi-tenant management and API key handling
  - `usage_service.py`: Usage logging and analytics

### Frontend (React/Vite)
- **Location**: `ui/`
- **Framework**: React 18 with Vite and Tailwind CSS
- **Key Pages**:
  - Dashboard: Usage statistics and analytics
  - Models: Available AI model catalog
  - Playground: Interactive API testing
  - API Keys: Key management
  - Tenants: Admin tenant management

### Database
- PostgreSQL with SQLAlchemy models
- Tables: tenants, api_keys, usage_logs, policies, provider_configs

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

## Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string
- `SESSION_SECRET` - JWT signing secret

Optional:
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `REDIS_URL` - Redis URL for rate limiting

## User Preferences

- Using Python 3.11+ with FastAPI
- React 18 with Vite and Tailwind CSS
- PostgreSQL for data persistence
- LiteLLM for multi-provider routing
