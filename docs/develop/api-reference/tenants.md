# Tenants API

Endpoints for managing tenants (organizations).

---

## List Tenants {#list}

*Admin only*

```http
GET /api/v1/admin/tenants
Authorization: Bearer ADMIN_TOKEN
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Acme Corp",
    "email": "admin@acme.com",
    "is_active": true,
    "is_admin": false,
    "rate_limit": 100,
    "monthly_budget": 1000.0,
    "current_spend": 45.67,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

## Get Tenant {#get}

```http
GET /api/v1/admin/tenants/{tenant_id}
Authorization: Bearer YOUR_TOKEN
```

---

## Update Tenant {#update}

```http
PATCH /api/v1/admin/tenants/{tenant_id}
Authorization: Bearer YOUR_TOKEN
```

**Request:**
```json
{
  "name": "Updated Name",
  "rate_limit": 500,
  "monthly_budget": 2000.0,
  "allowed_models": ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet"],
  "allowed_providers": ["openai", "anthropic"],
  "logging_policy": {
    "log_prompts": true,
    "log_responses": false,
    "retention_days": 30
  }
}
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Updated Name",
  "rate_limit": 500,
  "monthly_budget": 2000.0,
  "allowed_models": ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet"]
}
```

---

## Activate/Deactivate Tenant {#activate}

```http
POST /api/v1/admin/tenants/{tenant_id}/activate
Authorization: Bearer ADMIN_TOKEN
```

```http
POST /api/v1/admin/tenants/{tenant_id}/deactivate
Authorization: Bearer ADMIN_TOKEN
```
