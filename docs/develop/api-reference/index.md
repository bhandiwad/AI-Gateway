# API Reference

Complete reference for the AI Gateway API. All endpoints are prefixed with `/api/v1`.

---

## Authentication



-    **[Register](auth.md#register)**

    Create a new tenant account.

-    **[Login](auth.md#login)**

    Authenticate and get access token.

-    **[Current User](auth.md#current-user)**

    Get the currently authenticated user.

-    **[SSO](auth.md#sso)**

    Single sign-on endpoints.



---

## Chat



-    **[Chat Completions](chat.md)**

    OpenAI-compatible chat completion endpoint.

    ```
    POST /chat/completions
    ```



---

## Admin endpoints

### API Keys

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | [`/admin/api-keys`](api-keys.md#create) | Create API key |
| `GET` | [`/admin/api-keys`](api-keys.md#list) | List API keys |
| `DELETE` | [`/admin/api-keys/{id}`](api-keys.md#revoke) | Revoke API key |

### Tenants

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | [`/admin/tenants`](tenants.md#list) | List tenants (admin) |
| `GET` | [`/admin/tenants/{id}`](tenants.md#get) | Get tenant |
| `PATCH` | [`/admin/tenants/{id}`](tenants.md#update) | Update tenant |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | [`/admin/users`](users.md#list) | List users |
| `POST` | [`/admin/users`](users.md#create) | Create user |
| `PATCH` | [`/admin/users/{id}`](users.md#update) | Update user |
| `DELETE` | [`/admin/users/{id}`](users.md#delete) | Delete user |

### Guardrails

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | [`/admin/guardrails`](guardrails.md#list) | List guardrails |
| `POST` | [`/admin/guardrails/test`](guardrails.md#test) | Test guardrails |
| `GET` | [`/admin/guardrails/policies`](guardrails.md#policies) | List policies |

### Router

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | [`/admin/router/config`](router.md#config) | Get router config |
| `GET` | [`/admin/router/providers`](router.md#providers) | List providers |
| `GET` | [`/admin/router/health`](router.md#health) | Provider health |

### Usage & Billing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | [`/admin/usage/summary`](usage.md#summary) | Usage summary |
| `GET` | [`/admin/dashboard/stats`](usage.md#dashboard) | Dashboard stats |

### Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | [`/admin/audit-logs`](audit.md) | List audit logs |

---

## Health & Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/admin/features/status` | Feature status |

---

## Response format

All responses follow this structure:

=== "Success"

    ```json
    {
      "data": { ... },
      "meta": {
        "request_id": "abc123"
      }
    }
    ```

=== "Error"

    ```json
    {
      "detail": "Error message",
      "code": "ERROR_CODE"
    }
    ```

---

## Status codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not found |
| `422` | Validation error |
| `429` | Rate limited |
| `500` | Server error |

