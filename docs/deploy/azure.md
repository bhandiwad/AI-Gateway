# Azure Deployment

Deploy AI Gateway on Microsoft Azure.

---

## Deployment Options

| Service | Best For | Complexity |
|---------|----------|------------|
| **Container Apps** | Serverless containers | Low |
| **AKS** | Kubernetes workloads | Medium |
| **App Service** | PaaS deployment | Low |

---

## Container Apps (Recommended)

### Prerequisites

- Azure CLI installed
- Resource group created
- Container registry (ACR)

### 1. Create Container Registry

```bash
az acr create \
  --resource-group ai-gateway-rg \
  --name aigatewayacr \
  --sku Basic

az acr login --name aigatewayacr
```

### 2. Build and Push Image

```bash
# Build and push to ACR
az acr build \
  --registry aigatewayacr \
  --image ai-gateway:latest \
  --file Dockerfile .
```

### 3. Create Container Apps Environment

```bash
az containerapp env create \
  --name ai-gateway-env \
  --resource-group ai-gateway-rg \
  --location eastus
```

### 4. Deploy Container App

```bash
az containerapp create \
  --name ai-gateway \
  --resource-group ai-gateway-rg \
  --environment ai-gateway-env \
  --image aigatewayacr.azurecr.io/ai-gateway:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 1 \
  --memory 2Gi \
  --secrets \
    db-url="$DATABASE_URL" \
    jwt-secret="$JWT_SECRET" \
    openai-key="$OPENAI_API_KEY" \
  --env-vars \
    DATABASE_URL=secretref:db-url \
    JWT_SECRET_KEY=secretref:jwt-secret \
    OPENAI_API_KEY=secretref:openai-key \
    DEBUG=false
```

---

## Azure Database for PostgreSQL

```bash
az postgres flexible-server create \
  --resource-group ai-gateway-rg \
  --name ai-gateway-db \
  --location eastus \
  --admin-user adminuser \
  --admin-password $DB_PASSWORD \
  --sku-name Standard_B1ms \
  --storage-size 32

az postgres flexible-server db create \
  --resource-group ai-gateway-rg \
  --server-name ai-gateway-db \
  --database-name ai_gateway
```

---

## Azure Cache for Redis

```bash
az redis create \
  --resource-group ai-gateway-rg \
  --name ai-gateway-redis \
  --location eastus \
  --sku Basic \
  --vm-size c0
```

---

## Key Vault for Secrets

```bash
# Create Key Vault
az keyvault create \
  --resource-group ai-gateway-rg \
  --name ai-gateway-kv \
  --location eastus

# Add secrets
az keyvault secret set --vault-name ai-gateway-kv --name jwt-secret --value "$JWT_SECRET"
az keyvault secret set --vault-name ai-gateway-kv --name openai-key --value "$OPENAI_API_KEY"
```

---

## Custom Domain

```bash
az containerapp hostname add \
  --resource-group ai-gateway-rg \
  --name ai-gateway \
  --hostname gateway.yourcompany.com

az containerapp hostname bind \
  --resource-group ai-gateway-rg \
  --name ai-gateway \
  --hostname gateway.yourcompany.com \
  --environment ai-gateway-env \
  --validation-method CNAME
```

---

## Monitoring

### Application Insights

```bash
az monitor app-insights component create \
  --app ai-gateway-insights \
  --location eastus \
  --resource-group ai-gateway-rg
```

### Log Analytics

```bash
az containerapp logs show \
  --name ai-gateway \
  --resource-group ai-gateway-rg \
  --follow
```
