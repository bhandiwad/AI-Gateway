# Usage API

Endpoints for tracking usage and viewing statistics.

---

## Usage Summary {#summary}

```http
GET /api/v1/admin/usage/summary
Authorization: Bearer YOUR_TOKEN
```

**Query Parameters:**
- `start_date` - Start date (ISO format)
- `end_date` - End date (ISO format)
- `group_by` - Group by: `day`, `model`, `provider`

**Response (200):**
```json
{
  "total_requests": 15234,
  "total_tokens": 1523400,
  "prompt_tokens": 523400,
  "completion_tokens": 1000000,
  "total_cost": 45.67,
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  }
}
```

---

## Dashboard Stats {#dashboard}

```http
GET /api/v1/admin/dashboard/stats
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
```json
{
  "total_requests": 15234,
  "total_tokens": 1523400,
  "total_cost": 45.67,
  "requests_today": 523,
  "cost_today": 2.34,
  "active_api_keys": 5,
  "top_models": [
    {"model": "gpt-4o-mini", "requests": 8000},
    {"model": "gpt-4", "requests": 4000}
  ]
}
```

---

## Usage by Model

```http
GET /api/v1/admin/usage/by-model
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
```json
{
  "models": [
    {
      "model": "gpt-4o-mini",
      "requests": 8000,
      "tokens": 800000,
      "cost": 12.00
    },
    {
      "model": "gpt-4",
      "requests": 4000,
      "tokens": 400000,
      "cost": 24.00
    }
  ]
}
```

---

## Usage by Provider

```http
GET /api/v1/admin/usage/by-provider
Authorization: Bearer YOUR_TOKEN
```

---

## Export Usage

```http
GET /api/v1/admin/usage/export
Authorization: Bearer YOUR_TOKEN
```

**Query Parameters:**
- `format` - Export format: `csv`, `json`
- `start_date` - Start date
- `end_date` - End date

Returns downloadable file with usage data.
