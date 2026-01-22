# 🚢 Deployment Guide

This guide covers deploying AI Gateway in various environments from development to production.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Compose](#docker-compose)
4. [Kubernetes](#kubernetes)
5. [Cloud Deployments](#cloud-deployments)
6. [Production Checklist](#production-checklist)
7. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Multi-container orchestration |
| Python | 3.11+ | Backend runtime (local dev) |
| Node.js | 18+ | Frontend build (local dev) |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Caching and rate limiting |

### Required API Keys

At minimum, configure one AI provider:

- **OpenAI**: Get key from [platform.openai.com](https://platform.openai.com)
- **Anthropic**: Get key from [console.anthropic.com](https://console.anthropic.com)

---

## Local Development

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/your-org/ai-gateway.git
cd ai-gateway

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Start Infrastructure

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for services to be ready
docker-compose logs -f postgres redis
```

### 3. Backend Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run migrations
python -c "from backend.app.db.session import engine, Base; Base.metadata.create_all(bind=engine)"

# Start backend
uvicorn backend.app.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
# In a new terminal
cd ui
npm install
npm run dev
```

### 5. Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs
```

---

## Docker Compose

### Development Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Production-like Deployment

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: ai-gateway-backend:latest
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@postgres:5432/ai_gateway
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=false
      - LOG_LEVEL=INFO
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  frontend:
    image: ai-gateway-frontend:latest
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - backend
    restart: always

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=ai_gateway
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: always

volumes:
  postgres_data:
  redis_data:
```

Deploy:

```bash
# Set environment variables
export DB_PASSWORD=secure-db-password
export REDIS_PASSWORD=secure-redis-password
export JWT_SECRET_KEY=your-jwt-secret-at-least-32-chars
export OPENAI_API_KEY=sk-...

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

---

## Kubernetes

### Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- Helm 3.x (optional)

### Deployment Manifests

#### Namespace

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-gateway
```

#### Secrets

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-gateway-secrets
  namespace: ai-gateway
type: Opaque
stringData:
  DATABASE_URL: postgresql://user:password@postgres:5432/ai_gateway
  REDIS_URL: redis://:password@redis:6379/0
  JWT_SECRET_KEY: your-secret-key
  OPENAI_API_KEY: sk-...
```

#### ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-gateway-config
  namespace: ai-gateway
data:
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  ENABLE_TELEMETRY: "true"
  ENABLE_SEMANTIC_CACHE: "true"
```

#### Backend Deployment

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-gateway-backend
  namespace: ai-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-gateway-backend
  template:
    metadata:
      labels:
        app: ai-gateway-backend
    spec:
      containers:
      - name: backend
        image: your-registry/ai-gateway-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: ai-gateway-secrets
        - configMapRef:
            name: ai-gateway-config
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "2Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ai-gateway-backend
  namespace: ai-gateway
spec:
  selector:
    app: ai-gateway-backend
  ports:
  - port: 8000
    targetPort: 8000
```

#### Ingress

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-gateway-ingress
  namespace: ai-gateway
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - gateway.yourcompany.com
    secretName: ai-gateway-tls
  rules:
  - host: gateway.yourcompany.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: ai-gateway-backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-gateway-frontend
            port:
              number: 80
```

### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n ai-gateway

# View logs
kubectl logs -f deployment/ai-gateway-backend -n ai-gateway
```

---

## Cloud Deployments

### AWS (ECS/Fargate)

```bash
# Build and push images
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
docker build -t $ECR_REGISTRY/ai-gateway-backend .
docker push $ECR_REGISTRY/ai-gateway-backend

# Deploy with CloudFormation or Terraform
aws cloudformation deploy \
  --template-file aws/template.yaml \
  --stack-name ai-gateway \
  --parameter-overrides \
    DatabasePassword=$DB_PASSWORD \
    JWTSecretKey=$JWT_SECRET
```

### Google Cloud (Cloud Run)

```bash
# Build with Cloud Build
gcloud builds submit --tag gcr.io/$PROJECT_ID/ai-gateway-backend

# Deploy to Cloud Run
gcloud run deploy ai-gateway \
  --image gcr.io/$PROJECT_ID/ai-gateway-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL"
```

### Azure (Container Apps)

```bash
# Create container app environment
az containerapp env create \
  --name ai-gateway-env \
  --resource-group ai-gateway-rg \
  --location eastus

# Deploy backend
az containerapp create \
  --name ai-gateway-backend \
  --resource-group ai-gateway-rg \
  --environment ai-gateway-env \
  --image your-registry/ai-gateway-backend:latest \
  --target-port 8000 \
  --ingress external \
  --secrets database-url=$DATABASE_URL jwt-secret=$JWT_SECRET \
  --env-vars DATABASE_URL=secretref:database-url JWT_SECRET_KEY=secretref:jwt-secret
```

---

## Production Checklist

### Security

- [ ] **HTTPS enabled** with valid SSL certificates
- [ ] **JWT secret** is cryptographically strong (32+ characters)
- [ ] **Database password** is strong and unique
- [ ] **API keys** stored securely (secrets manager)
- [ ] **CORS** configured for specific origins only
- [ ] **Rate limiting** enabled
- [ ] **Debug mode** disabled
- [ ] **Firewall rules** restrict database/Redis access

### Performance

- [ ] **Database connection pooling** configured
- [ ] **Redis caching** enabled
- [ ] **Multiple backend replicas** running
- [ ] **Load balancer** configured with health checks
- [ ] **Resource limits** set appropriately
- [ ] **Horizontal Pod Autoscaler** (Kubernetes) configured

### Reliability

- [ ] **Health checks** configured
- [ ] **Liveness/readiness probes** set up
- [ ] **Automatic restarts** enabled
- [ ] **Database backups** scheduled
- [ ] **Disaster recovery plan** documented
- [ ] **Circuit breakers** enabled for providers

### Observability

- [ ] **Structured logging** enabled
- [ ] **Log aggregation** configured (ELK, CloudWatch, etc.)
- [ ] **Metrics collection** enabled
- [ ] **Alerting rules** configured
- [ ] **Distributed tracing** enabled (optional)

### Compliance

- [ ] **Audit logging** enabled
- [ ] **PII redaction** in logs enabled
- [ ] **Data retention policies** configured
- [ ] **Access controls** properly configured
- [ ] **Security scanning** in CI/CD pipeline

---

## Monitoring & Maintenance

### Health Checks

```bash
# Basic health
curl https://gateway.yourcompany.com/health

# Detailed metrics
curl https://gateway.yourcompany.com/metrics

# Feature status
curl -H "Authorization: Bearer $TOKEN" \
  https://gateway.yourcompany.com/api/v1/admin/features/status
```

### Log Analysis

```bash
# Docker Compose logs
docker-compose logs -f backend | grep -E "(ERROR|WARN)"

# Kubernetes logs
kubectl logs -f -l app=ai-gateway-backend -n ai-gateway --tail=100
```

### Database Maintenance

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres ai_gateway > backup.sql

# Vacuum database
docker-compose exec postgres psql -U postgres -d ai_gateway -c "VACUUM ANALYZE;"
```

### Updates

```bash
# Pull latest images
docker-compose pull

# Rolling restart
docker-compose up -d --no-deps backend

# Kubernetes rolling update
kubectl rollout restart deployment/ai-gateway-backend -n ai-gateway
kubectl rollout status deployment/ai-gateway-backend -n ai-gateway
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

```bash
# Check database is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U postgres -d ai_gateway -c "SELECT 1;"

# Check connection string
echo $DATABASE_URL
```

#### Redis Connection Failed

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

#### API Returns 500 Errors

```bash
# Check backend logs
docker-compose logs backend --tail=50

# Enable debug mode temporarily
docker-compose exec backend sh -c "LOG_LEVEL=DEBUG uvicorn backend.app.main:app"
```

#### Slow Response Times

```bash
# Check resource usage
docker stats

# Check database slow queries
docker-compose exec postgres psql -U postgres -d ai_gateway -c "SELECT * FROM pg_stat_activity;"
```

