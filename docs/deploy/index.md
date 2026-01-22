# Deploy

Deploy AI Gateway to production with confidence. Choose from Docker, Kubernetes, or major cloud platforms.

---

## Deployment options



-    **Docker**

    ---

    Simple deployment using Docker Compose. Perfect for small to medium workloads.

    [ Docker Guide](docker.md)

-    **Kubernetes**

    ---

    Scalable deployment on Kubernetes with Helm charts. For enterprise workloads.

    [ Kubernetes Guide](kubernetes.md)

-    **AWS**

    ---

    Deploy on AWS using ECS, Fargate, or EKS.

    [ AWS Guide](aws.md)

-    **Google Cloud**

    ---

    Deploy on GCP using Cloud Run or GKE.

    [ GCP Guide](gcp.md)

-    **Azure**

    ---

    Deploy on Azure using Container Apps or AKS.

    [ Azure Guide](azure.md)



---

## Quick comparison

| Option | Best for | Scaling | Complexity |
|--------|----------|---------|------------|
| Docker Compose | Development, small teams | Manual | Low |
| Kubernetes | Enterprise, high availability | Auto | High |
| AWS ECS | AWS-native, managed containers | Auto | Medium |
| Cloud Run | Serverless, pay-per-use | Auto | Low |
| Azure Container Apps | Azure-native, serverless | Auto | Low |

---

## Production checklist

Before deploying to production, ensure you've completed these items:

### Security

- [ ] HTTPS enabled with valid SSL certificates
- [ ] Strong JWT secret (32+ characters)
- [ ] Secure database password
- [ ] API keys stored in secrets manager
- [ ] CORS configured for specific origins
- [ ] Debug mode disabled

### Performance

- [ ] Database connection pooling configured
- [ ] Redis caching enabled
- [ ] Multiple backend replicas
- [ ] Resource limits configured
- [ ] Health checks enabled

### Reliability

- [ ] Automatic restarts enabled
- [ ] Database backups scheduled
- [ ] Circuit breakers enabled
- [ ] Alerting configured

### Compliance

- [ ] Audit logging enabled
- [ ] PII redaction in logs
- [ ] Data retention policies set

---

## Environment variables

Essential configuration for production:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/ai_gateway

# Redis
REDIS_URL=redis://:password@host:6379/0

# Security
JWT_SECRET_KEY=your-production-secret-key-minimum-32-chars

# Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Production settings
DEBUG=false
LOG_LEVEL=INFO
```

See [Configuration Reference](../develop/concepts/configuration.md) for all options.

---

## Monitoring

### Health endpoint

```bash
curl https://your-gateway.com/health
# {"status": "healthy"}
```

### Metrics

Prometheus-compatible metrics at `/metrics`:

```bash
curl https://your-gateway.com/metrics
```

### Recommended tools

| Tool | Purpose |
|------|---------|
| Prometheus | Metrics collection |
| Grafana | Dashboards |
| Jaeger | Distributed tracing |
| ELK Stack | Log aggregation |

