# AWS Deployment

Deploy AI Gateway on Amazon Web Services.

---

## Deployment Options

| Service | Best For | Complexity |
|---------|----------|------------|
| **ECS Fargate** | Serverless containers | Low |
| **EKS** | Kubernetes workloads | Medium |
| **EC2** | Full control | High |

---

## ECS Fargate (Recommended)

### Prerequisites

- AWS CLI configured
- ECR repository created
- VPC with subnets

### 1. Push Image to ECR

```bash
# Authenticate
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t ai-gateway-backend .
docker tag ai-gateway-backend:latest $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ai-gateway:latest
docker push $AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ai-gateway:latest
```

### 2. Create Task Definition

```json
{
  "family": "ai-gateway",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "ai-gateway",
      "image": "${AWS_ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com/ai-gateway:latest",
      "portMappings": [
        {"containerPort": 8000, "protocol": "tcp"}
      ],
      "environment": [
        {"name": "DEBUG", "value": "false"}
      ],
      "secrets": [
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "JWT_SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-gateway",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 3. Create Service

```bash
aws ecs create-service \
  --cluster ai-gateway-cluster \
  --service-name ai-gateway \
  --task-definition ai-gateway:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### 4. Add Load Balancer

```bash
aws elbv2 create-load-balancer \
  --name ai-gateway-alb \
  --type application \
  --subnets subnet-xxx subnet-yyy
```

---

## Infrastructure as Code

### Terraform

```hcl
module "ai_gateway" {
  source = "your-org/ai-gateway/aws"
  
  cluster_name    = "ai-gateway"
  vpc_id          = var.vpc_id
  subnet_ids      = var.subnet_ids
  
  database_url    = var.database_url
  jwt_secret_key  = var.jwt_secret_key
  openai_api_key  = var.openai_api_key
}
```

### CloudFormation

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: AI Gateway on ECS Fargate

Resources:
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: ai-gateway

  TaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      Family: ai-gateway
      Cpu: '1024'
      Memory: '2048'
      NetworkMode: awsvpc
      RequiresCompatibilities:
        - FARGATE
```

---

## RDS for PostgreSQL

```bash
aws rds create-db-instance \
  --db-instance-identifier ai-gateway-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username admin \
  --master-user-password $DB_PASSWORD \
  --allocated-storage 20
```

---

## ElastiCache for Redis

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id ai-gateway-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```
