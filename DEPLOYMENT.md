# Local Deployment Guide

## Prerequisites

- Docker Desktop installed and running
- 8GB+ RAM available
- Ports 80, 8000, 5432, 6379 available

---

## Quick Start (Easiest)

### 1. Make the deployment script executable:
```bash
chmod +x deploy-local.sh
```

### 2. Run the deployment script:
```bash
./deploy-local.sh
```

That's it! The script will:
- ✅ Create `.env` file if missing
- ✅ Build all containers
- ✅ Start backend, frontend, PostgreSQL, Redis
- ✅ Show you service URLs and logs

---

## Manual Deployment

### 1. Create environment file:
```bash
cp .env.example .env
```

### 2. (Optional) Add your AI provider API keys:
Edit `.env` and add:
```bash
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Note:** API keys are optional. The gateway has mock providers for testing without real API keys.

### 3. Start all services:
```bash
docker-compose up -d
```

### 4. Check status:
```bash
docker-compose ps
```

---

## Access the Gateway

### Backend API
- **URL:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### Frontend UI
- **URL:** http://localhost:80

### Databases
- **PostgreSQL:** localhost:5432 (postgres/postgres)
- **Redis:** localhost:6379

---

## Testing Phase 1 Features

### 1. Health Dashboard
```bash
curl http://localhost:8000/api/v1/admin/router/health-dashboard
```

### 2. Circuit Breaker Status
```bash
curl http://localhost:8000/api/v1/admin/router/circuit-breakers
```

### 3. Load Balancer Stats
```bash
curl http://localhost:8000/api/v1/admin/router/load-balancer/stats
```

### 4. Create Test Tenant & API Key
```bash
# Create tenant
curl -X POST http://localhost:8000/api/v1/admin/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Create API key
curl -X POST http://localhost:8000/api/v1/admin/api-keys \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": 1,
    "name": "Test Key",
    "cost_limit_daily": 10.0,
    "cost_limit_monthly": 100.0
  }'
```

### 5. Test Chat Completion (with mock provider)
```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'
```

### 6. Test Error Handling - Quota Exceeded
```bash
# Make requests until daily limit is hit
# Watch for 402 Payment Required response with user-friendly error
```

### 7. Test Circuit Breaker
```bash
# Force circuit breaker open
curl -X POST http://localhost:8000/api/v1/admin/router/circuit-breakers/openai/force-open

# Try chat completion - should fail with circuit breaker error
# Then force close
curl -X POST http://localhost:8000/api/v1/admin/router/circuit-breakers/openai/force-close
```

### 8. Register Load Balancer Pool
```bash
curl -X POST http://localhost:8000/api/v1/admin/router/load-balancer/pools \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "gpt-4",
    "providers": [
      {"name": "openai-primary", "weight": 70},
      {"name": "openai-backup", "weight": 30}
    ],
    "strategy": "weighted_round_robin"
  }'
```

---

## View Logs

### All services:
```bash
docker-compose logs -f
```

### Backend only:
```bash
docker-compose logs -f backend
```

### Frontend only:
```bash
docker-compose logs -f frontend
```

### Filter for errors:
```bash
docker-compose logs -f | grep -i error
```

---

## Database Access

### Connect to PostgreSQL:
```bash
docker-compose exec postgres psql -U postgres -d ai_gateway
```

### View tables:
```sql
\dt
```

### Check API keys:
```sql
SELECT id, name, key_prefix, cost_limit_daily, cost_limit_monthly FROM api_keys;
```

### Check usage logs:
```sql
SELECT * FROM usage_logs ORDER BY created_at DESC LIMIT 10;
```

---

## Troubleshooting

### Port already in use:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Container won't start:
```bash
# View detailed logs
docker-compose logs backend

# Rebuild without cache
docker-compose build --no-cache

# Remove all containers and volumes
docker-compose down -v
docker-compose up -d
```

### Database connection error:
```bash
# Wait a bit longer for PostgreSQL to initialize
sleep 10

# Or check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres
```

### Import errors in Python:
```bash
# Rebuild the backend container
docker-compose build backend
docker-compose up -d backend
```

---

## Stop Services

### Stop all:
```bash
docker-compose down
```

### Stop and remove volumes (fresh start):
```bash
docker-compose down -v
```

### Stop but keep data:
```bash
docker-compose stop
```

### Restart after changes:
```bash
docker-compose restart backend
```

---

## Performance Tips

### View resource usage:
```bash
docker stats
```

### Limit container resources (add to docker-compose.yml):
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## Development Workflow

### Hot reload is enabled for backend:
1. Make changes to Python files
2. Changes auto-reload (volume mounted)
3. Check logs: `docker-compose logs -f backend`

### Frontend changes:
1. Make changes to React files in `ui/`
2. Rebuild: `docker-compose build frontend`
3. Restart: `docker-compose restart frontend`

---

## Next Steps

1. ✅ Deploy locally
2. ✅ Test basic health endpoints
3. ✅ Create tenant and API key
4. ✅ Test Phase 1 features (load balancer, circuit breaker)
5. ✅ Test error handling (quota limits, payment errors)
6. ✅ Review logs for any issues
7. 📝 Add your real API keys to test with actual providers
8. 🎨 Update frontend to show new features

---

## Production Deployment

For production deployment:
1. Update `.env` with production values
2. Set strong `SESSION_SECRET`
3. Add real AI provider API keys
4. Configure proper domain and SSL
5. Set up monitoring (Prometheus/Grafana)
6. Enable backup for PostgreSQL
7. Review security settings

See `docs/PRODUCTION_DEPLOYMENT.md` for detailed guide.
