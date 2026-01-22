# Installation

This guide covers all installation options for AI Gateway.

---

## Docker (Recommended)

The fastest way to get started is using Docker Compose.

### Step 1: Clone the repository

```bash
git clone https://github.com/your-org/ai-gateway.git
cd ai-gateway
```

### Step 2: Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Required
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ai_gateway
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-secret-key-at-least-32-characters

# At least one provider
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Step 3: Start services

```bash
docker-compose up -d
```

### Step 4: Verify installation

```bash
# Check health
curl http://localhost:8000/health

# Expected response
{"status": "healthy"}
```

✓ **Done!** Access the dashboard at http://localhost

---

## Local development

For contributing or customizing AI Gateway.

### Backend setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Start infrastructure
docker-compose up -d postgres redis

# Run backend
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend setup

```bash
cd ui
npm install
npm run dev
```

---

## Kubernetes

For production deployments at scale.

### Using Helm

```bash
helm repo add ai-gateway https://your-org.github.io/ai-gateway-helm
helm install ai-gateway ai-gateway/ai-gateway \
  --set secrets.jwtSecretKey=$JWT_SECRET \
  --set secrets.openaiApiKey=$OPENAI_API_KEY
```

### Using manifests

```bash
kubectl apply -f k8s/
```

See the [Kubernetes deployment guide](../deploy/kubernetes.md) for detailed instructions.

---

## Cloud platforms

| Platform | Guide |
|----------|-------|
| AWS ECS/Fargate | [AWS Deployment](../deploy/aws.md) |
| Google Cloud Run | [GCP Deployment](../deploy/gcp.md) |
| Azure Container Apps | [Azure Deployment](../deploy/azure.md) |

---

## Verify installation

After installation, verify everything is working:

```bash
# 1. Check health endpoint
curl http://localhost:8000/health

# 2. Check API docs
open http://localhost:8000/docs

# 3. Register a user
curl -X POST http://localhost:8000/api/v1/admin/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email": "test@example.com", "password": "Password123!"}'
```

---

## Troubleshooting

??? question "Port 8000 is already in use"
    Stop any service using port 8000, or change the port in `docker-compose.yml`:
    ```yaml
    ports:
      - "8001:8000"  # Use port 8001 instead
    ```

??? question "Database connection failed"
    Ensure PostgreSQL is running and the connection string is correct:
    ```bash
    docker-compose ps postgres
    docker-compose logs postgres
    ```

??? question "Redis connection failed"
    Verify Redis is running:
    ```bash
    docker-compose exec redis redis-cli ping
    # Should return: PONG
    ```

---

## Next steps

 [Quickstart](quickstart.md) - Make your first API call

