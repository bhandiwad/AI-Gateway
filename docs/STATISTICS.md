# Statistics & Analytics

The AI Gateway provides comprehensive statistics and analytics to help you understand usage patterns, costs, and performance across your organization.

## Accessing Statistics

Navigate to **Statistics** in the sidebar or visit `/stats` in the dashboard.

## Overview Tab

The overview tab provides a high-level summary of your usage:

### Key Metrics
- **Total Requests** - Number of API calls in the selected period
- **Total Tokens** - Combined prompt + completion tokens
- **Total Cost** - Displayed in ₹ (INR) with USD conversion
- **Avg Latency** - Average response time in milliseconds
- **Success Rate** - Percentage of successful requests

### Time Period Selection
Choose from:
- Last 7 days
- Last 30 days
- Last 90 days

### Visualizations
- **Hourly Distribution** - Bar chart showing request patterns by hour
- **Error Breakdown** - Success vs errors vs cache hits

---

## Models Tab

Track usage across all AI models:

| Column | Description |
|--------|-------------|
| Model | Model name (e.g., gpt-4o-mini, claude-3-sonnet) |
| Provider | OpenAI, Anthropic, Google, etc. |
| Requests | Total number of requests |
| Tokens | Total tokens consumed |
| Cost | Cost in ₹ (INR) |
| Avg Latency | Average response time |

---

## API Keys Tab

Monitor usage per API key:

| Column | Description |
|--------|-------------|
| API Key | Key name |
| Requests | Total requests made with this key |
| Tokens | Total tokens consumed |
| Cost | Cost in ₹ (INR) |
| Avg Latency | Average response time |
| Success Rate | Percentage of successful requests |

Use this to identify:
- Which applications are consuming the most resources
- Keys with high error rates that need attention
- Unused or underutilized keys

---

## Users Tab

Track usage by individual users:

| Column | Description |
|--------|-------------|
| User | User name |
| Email | User email |
| Requests | Total requests |
| Tokens | Total tokens consumed |
| Cost | Cost in ₹ (INR) |

---

## Departments Tab

Aggregate usage by department for cost allocation:

| Column | Description |
|--------|-------------|
| Department | Department name |
| Requests | Total requests |
| Tokens | Total tokens consumed |
| Cost | Cost in ₹ (INR) |

### Cost Distribution Chart
A pie chart showing the percentage of total cost attributed to each department.

---

## Cache Tab

Manage and monitor the semantic cache:

### Cache Statistics
- **Cache Hits** - Requests served from cache
- **Cache Misses** - Requests that required provider calls
- **Hit Rate** - Percentage of requests served from cache
- **Tokens Saved** - Estimated tokens saved from cache hits
- **Cost Saved** - Estimated cost savings in ₹ (INR)

### Cache Configuration
| Setting | Value | Description |
|---------|-------|-------------|
| TTL | 1 hour | How long entries are cached |
| Max Size | 10,000 | Maximum entries in cache |
| Similarity Threshold | 92% | Minimum match score for semantic hits |

### Cache Management
- **Refresh** - Reload cache statistics
- **Clear Cache** - Remove all cached entries (requires confirmation)

---

## Performance Tab

Monitor system health and performance:

### Metrics
- **Avg Response Time** - Average latency across all requests
- **Success Rate** - Overall success percentage
- **Cache Hit Rate** - Semantic cache performance
- **Requests/Day** - Average daily request volume

### System Health
Visual indicators for:
- API Gateway status
- Cache Service status
- Load Balancer status

---

## API Endpoints

### Get Detailed Statistics
```bash
GET /api/v1/admin/stats/detailed?days=30
Authorization: Bearer YOUR_TOKEN
```

Response:
```json
{
  "summary": {
    "total_requests": 1500,
    "total_tokens": 450000,
    "total_cost": 12.50,
    "avg_latency_ms": 850,
    "success_rate": 99.2
  },
  "top_models": [...],
  "by_api_key": [...],
  "by_user": [...],
  "by_department": [...],
  "hourly_distribution": [...],
  "error_breakdown": {...}
}
```

### Get Cache Statistics
```bash
GET /api/v1/admin/cache/stats
Authorization: Bearer YOUR_TOKEN
```

Response:
```json
{
  "enabled": true,
  "hits": 250,
  "misses": 1250,
  "hit_rate": 16.67,
  "tokens_saved": 75000,
  "cost_saved_usd": 1.50,
  "cost_saved_inr": 125.25,
  "cache_size": 500
}
```

---

## Currency Display

All costs are displayed in **Indian Rupees (₹ INR)** throughout the UI. The conversion rate used is:

```
1 USD = 83.5 INR
```

USD values are shown as secondary information where applicable.
