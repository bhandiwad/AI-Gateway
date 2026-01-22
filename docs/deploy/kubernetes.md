# Kubernetes Deployment

Deploy AI Gateway on Kubernetes for production-scale workloads.

---

## Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured
- Helm 3.x (optional)

---

## Quick Start with Helm

```bash
# Add the Helm repository
helm repo add ai-gateway https://your-org.github.io/ai-gateway-helm
helm repo update

# Install AI Gateway
helm install ai-gateway ai-gateway/ai-gateway \
  --namespace ai-gateway \
  --create-namespace \
  --set secrets.jwtSecretKey=$JWT_SECRET \
  --set secrets.openaiApiKey=$OPENAI_API_KEY \
  --set secrets.databaseUrl=$DATABASE_URL
```

---

## Manual Deployment

### 1. Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-gateway
```

### 2. Create Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-gateway-secrets
  namespace: ai-gateway
type: Opaque
stringData:
  DATABASE_URL: postgresql://user:password@postgres:5432/ai_gateway
  REDIS_URL: redis://:password@redis:6379/0
  JWT_SECRET_KEY: your-secret-key-minimum-32-characters
  OPENAI_API_KEY: sk-...
```

### 3. Create ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-gateway-config
  namespace: ai-gateway
data:
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  ENABLE_TELEMETRY: "true"
```

### 4. Deploy Backend

```yaml
# backend-deployment.yaml
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

### 5. Create Ingress

```yaml
# ingress.yaml
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
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-gateway-backend
            port:
              number: 8000
```

### 6. Apply Manifests

```bash
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f ingress.yaml
```

---

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ai-gateway-hpa
  namespace: ai-gateway
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ai-gateway-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Monitoring

```bash
# Check pod status
kubectl get pods -n ai-gateway

# View logs
kubectl logs -f deployment/ai-gateway-backend -n ai-gateway

# Check health
kubectl exec -it deployment/ai-gateway-backend -n ai-gateway -- curl localhost:8000/health
```
