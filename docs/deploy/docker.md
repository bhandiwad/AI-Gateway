# Docker Deployment

Deploy AI Gateway using Docker and Docker Compose.

---

## Prerequisites

- Docker 24.0+
- Docker Compose 2.20+
- At least one AI provider API key

---

## Quick start

### 1. Clone and configure

```bash
git clone https://github.com/your-org/ai-gateway.git
cd ai-gateway

cp .env.example .env
# Edit .env with your settings
```

### 2. Start services

```bash
docker-compose up -d
```

### 3. Verify

```bash
curl http://localhost:8000/health
```

 AI Gateway is running!

---

## Production configuration

For production, create `docker-compose.prod.yml`:

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

  frontend:
    image: ai-gateway-frontend:latest
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    restart: always

  postgres:
    image: postgres:15-alpine
    environment:
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

### Deploy

```bash
export DB_PASSWORD=secure-password
export REDIS_PASSWORD=secure-password
export JWT_SECRET_KEY=your-32-char-secret
export OPENAI_API_KEY=sk-...

docker-compose -f docker-compose.prod.yml up -d
```

---

## SSL/HTTPS

### Using Traefik

Add Traefik as reverse proxy with automatic SSL:

```yaml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=you@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt

  backend:
    labels:
      - "traefik.http.routers.backend.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
```

---

## Scaling

### Horizontal scaling

```bash
docker-compose up -d --scale backend=3
```

### With load balancer

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend

  backend:
    deploy:
      replicas: 3
```

---

## Maintenance

### View logs

```bash
docker-compose logs -f backend
```

### Backup database

```bash
docker-compose exec postgres pg_dump -U postgres ai_gateway > backup.sql
```

### Update

```bash
docker-compose pull
docker-compose up -d
```

### Restart

```bash
docker-compose restart backend
```

---

## Troubleshooting

??? question "Container keeps restarting"
    Check logs for errors:
    ```bash
    docker-compose logs backend --tail=50
    ```

??? question "Cannot connect to database"
    Verify PostgreSQL is healthy:
    ```bash
    docker-compose ps postgres
    docker-compose exec postgres pg_isready
    ```

??? question "Out of memory"
    Increase memory limits in docker-compose.yml:
    ```yaml
    deploy:
      resources:
        limits:
          memory: 4G
    ```

