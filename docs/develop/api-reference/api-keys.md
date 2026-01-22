# API Keys

Endpoints for creating and managing API keys.

---

## Create API Key {#create}

```http
POST /api/v1/admin/api-keys
Authorization: Bearer YOUR_TOKEN
```

**Request:**
```json
{
  "name": "Production Key",
  "description": "Key for production environment",
  "environment": "production",
  "rate_limit_override": 500,
  "allowed_models_override": ["gpt-4", "gpt-3.5-turbo"],
  "cost_limit_daily": 50.0,
  "cost_limit_monthly": 500.0
}
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Production Key",
  "api_key": "sk-gw-abc123...",
  "key_prefix": "sk-gw-abc",
  "is_active": true,
  "environment": "production",
  "rate_limit_override": 500,
  "created_at": "2024-01-15T10:30:00Z"
}
```

> **Note:** The full `api_key` is only returned once at creation. Store it securely.

---

## List API Keys {#list}

```http
GET /api/v1/admin/api-keys
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Production Key",
    "key_prefix": "sk-gw-abc",
    "is_active": true,
    "environment": "production",
    "last_used_at": "2024-01-15T12:00:00Z",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

## Get API Key {#get}

```http
GET /api/v1/admin/api-keys/{key_id}
Authorization: Bearer YOUR_TOKEN
```

---

## Revoke API Key {#revoke}

```http
DELETE /api/v1/admin/api-keys/{key_id}
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
```json
{
  "message": "API key revoked successfully"
}
```

---

## Using API Keys

Include your API key in the Authorization header:

```bash
curl http://localhost:8000/api/v1/chat/completions \
  -H "Authorization: Bearer sk-gw-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}'
```
