# Google Cloud Deployment

Deploy AI Gateway on Google Cloud Platform.

---

## Deployment Options

| Service | Best For | Complexity |
|---------|----------|------------|
| **Cloud Run** | Serverless, auto-scaling | Low |
| **GKE** | Kubernetes workloads | Medium |
| **Compute Engine** | Full control | High |

---

## Cloud Run (Recommended)

### Prerequisites

- gcloud CLI installed and configured
- Project with billing enabled
- Artifact Registry repository

### 1. Build and Push Image

```bash
# Configure Docker for Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build with Cloud Build
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/ai-gateway/backend:latest
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy ai-gateway \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/ai-gateway/backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DEBUG=false,LOG_LEVEL=INFO" \
  --set-secrets "DATABASE_URL=ai-gateway-db-url:latest" \
  --set-secrets "JWT_SECRET_KEY=ai-gateway-jwt:latest" \
  --set-secrets "OPENAI_API_KEY=openai-key:latest" \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10
```

### 3. Set Up Custom Domain

```bash
gcloud run domain-mappings create \
  --service ai-gateway \
  --domain gateway.yourcompany.com \
  --region us-central1
```

---

## Cloud SQL for PostgreSQL

### Create Instance

```bash
gcloud sql instances create ai-gateway-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-4096 \
  --region=us-central1 \
  --root-password=$DB_PASSWORD

gcloud sql databases create ai_gateway \
  --instance=ai-gateway-db
```

### Connect from Cloud Run

```bash
gcloud run services update ai-gateway \
  --add-cloudsql-instances=$PROJECT_ID:us-central1:ai-gateway-db \
  --set-env-vars "DATABASE_URL=postgresql://user:pass@/ai_gateway?host=/cloudsql/$PROJECT_ID:us-central1:ai-gateway-db"
```

---

## Memorystore for Redis

```bash
gcloud redis instances create ai-gateway-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

---

## Secret Manager

### Create Secrets

```bash
# Create secrets
echo -n "your-jwt-secret" | gcloud secrets create ai-gateway-jwt --data-file=-
echo -n "sk-..." | gcloud secrets create openai-key --data-file=-
echo -n "postgresql://..." | gcloud secrets create ai-gateway-db-url --data-file=-

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding ai-gateway-jwt \
  --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Monitoring

### Cloud Logging

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-gateway" \
  --limit=50
```

### Cloud Monitoring

Set up alerts for:
- Request latency > 2s
- Error rate > 5%
- CPU utilization > 80%
