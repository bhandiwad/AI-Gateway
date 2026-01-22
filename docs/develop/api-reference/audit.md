# Audit Logs API

Endpoints for retrieving audit logs.

---

## List Audit Logs

```http
GET /api/v1/admin/audit-logs
Authorization: Bearer YOUR_TOKEN
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Filter by action type |
| `user_id` | integer | Filter by user ID |
| `start_date` | string | Start date (ISO format) |
| `end_date` | string | End date (ISO format) |
| `limit` | integer | Max results (default: 100) |
| `offset` | integer | Pagination offset |

**Response (200):**
```json
{
  "logs": [
    {
      "id": 1,
      "action": "api_key_created",
      "actor_id": 1,
      "actor_email": "admin@example.com",
      "resource_type": "api_key",
      "resource_id": "5",
      "details": {
        "key_name": "Production Key"
      },
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

---

## Action Types

| Action | Description |
|--------|-------------|
| `user_login` | User logged in |
| `user_logout` | User logged out |
| `api_key_created` | API key created |
| `api_key_revoked` | API key revoked |
| `tenant_updated` | Tenant settings updated |
| `user_created` | User created |
| `user_deleted` | User deleted |
| `guardrail_triggered` | Guardrail blocked/modified content |
| `rate_limit_exceeded` | Rate limit was exceeded |

---

## Export Audit Logs

```http
GET /api/v1/admin/audit-logs/export
Authorization: Bearer YOUR_TOKEN
```

**Query Parameters:**
- `format` - Export format: `csv`, `json`
- `start_date` - Start date
- `end_date` - End date

Returns downloadable file with audit logs for compliance reporting.
