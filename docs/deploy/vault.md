# HashiCorp Vault Integration

AI Gateway supports HashiCorp Vault for secure secrets management.

---

## Overview

| Feature | Description |
|---------|-------------|
| **Vault KV v2** | Secrets stored in Key-Value v2 engine |
| **Auth Methods** | Token or AppRole authentication |
| **Fallback** | Automatic fallback to environment variables |
| **Caching** | Local cache with 5-minute TTL |

---

## Quick Setup

### 1. Start Vault (Development)

```bash
# Run Vault in dev mode
docker run -d --name vault \
  -p 8200:8200 \
  -e VAULT_DEV_ROOT_TOKEN_ID=dev-token \
  hashicorp/vault:latest

# Set environment
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=dev-token
```

### 2. Store Secrets in Vault

```bash
# Enable KV v2 (if not already)
vault secrets enable -path=secret kv-v2

# Store AI Gateway secrets
vault kv put secret/ai-gateway \
  OPENAI_API_KEY=sk-your-openai-key \
  ANTHROPIC_API_KEY=sk-ant-your-anthropic-key \
  SESSION_SECRET=your-production-secret-key \
  DATABASE_PASSWORD=your-db-password
```

### 3. Configure AI Gateway

Add to `.env`:

```bash
VAULT_ENABLED=true
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=dev-token
VAULT_SECRET_PATH=ai-gateway
```

### 4. Restart Backend

```bash
docker-compose restart backend
```

---

## Authentication Methods

### Token-Based (Development)

```bash
VAULT_ENABLED=true
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=hvs.your-vault-token
```

### AppRole (Production Recommended)

```bash
# Create AppRole in Vault
vault auth enable approle

vault write auth/approle/role/ai-gateway \
  token_policies="ai-gateway-policy" \
  token_ttl=1h \
  token_max_ttl=4h

# Get Role ID and Secret ID
vault read auth/approle/role/ai-gateway/role-id
vault write -f auth/approle/role/ai-gateway/secret-id
```

Configure in `.env`:

```bash
VAULT_ENABLED=true
VAULT_ADDR=http://vault:8200
VAULT_ROLE_ID=your-role-id
VAULT_SECRET_ID=your-secret-id
```

---

## Vault Policy

Create a policy for AI Gateway:

```hcl
# ai-gateway-policy.hcl
path "secret/data/ai-gateway" {
  capabilities = ["read", "list"]
}

path "secret/data/ai-gateway/*" {
  capabilities = ["read", "list"]
}
```

Apply the policy:

```bash
vault policy write ai-gateway-policy ai-gateway-policy.hcl
```

---

## Docker Compose with Vault

Add Vault to `docker-compose.yml`:

```yaml
services:
  vault:
    image: hashicorp/vault:latest
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: dev-token
      VAULT_DEV_LISTEN_ADDRESS: 0.0.0.0:8200
    cap_add:
      - IPC_LOCK
    volumes:
      - vault_data:/vault/data

volumes:
  vault_data:
```

Update backend environment:

```yaml
  backend:
    environment:
      VAULT_ENABLED: "true"
      VAULT_ADDR: http://vault:8200
      VAULT_TOKEN: dev-token
```

---

## Secrets Reference

| Secret Key | Description |
|------------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `SESSION_SECRET` | JWT signing key |
| `DATABASE_PASSWORD` | PostgreSQL password |

---

## Verification

Check if Vault is connected:

```bash
curl http://localhost/api/v1/health
```

Response includes:

```json
{
  "secrets": {
    "vault_enabled": true,
    "vault_connected": true
  }
}
```

---

## Troubleshooting

### Vault Connection Failed

```
vault_connection_failed: Connection refused
```

- Check `VAULT_ADDR` is reachable
- Verify Vault is running: `vault status`
- Check network connectivity between containers

### Authentication Failed

```
vault_authentication_failed
```

- Verify token is valid: `vault token lookup`
- Check AppRole credentials
- Ensure policy allows access to secret path

### Secret Not Found

Falls back to environment variable automatically. Check logs:

```
secret_fetched_from_vault key=OPENAI_API_KEY
```

or

```
Using environment variables for secrets
```

---

## Production Checklist

- [ ] Use AppRole authentication (not tokens)
- [ ] Enable Vault audit logging
- [ ] Configure secret rotation
- [ ] Use TLS for Vault communication
- [ ] Set up Vault HA cluster
- [ ] Implement secret versioning
- [ ] Configure automatic unsealing
