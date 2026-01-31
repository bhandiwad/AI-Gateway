# Prompt Caching

The AI Gateway includes a semantic caching system that can significantly reduce API costs by reusing responses for similar prompts.

## Overview

When a user sends a chat request, the system:

1. Computes an embedding for the prompt
2. Searches for semantically similar cached responses
3. Returns cached response if similarity exceeds threshold (92%)
4. Otherwise, calls the provider and caches the new response

## Benefits

- **Reduced API Costs** - Avoid redundant calls to expensive models
- **Lower Latency** - Cached responses return instantly
- **Consistent Responses** - Same question gets same answer

## Enabling Semantic Cache

Set the environment variable:

```bash
ENABLE_SEMANTIC_CACHE=true
```

Or in your `.env` file:

```env
ENABLE_SEMANTIC_CACHE=true
```

## How It Works

### Cache Lookup Flow

```
User Request → Compute Embedding → Search Cache
                                       ↓
                              Similar Found? (≥92%)
                                    ↓         ↓
                                   Yes        No
                                    ↓         ↓
                            Return Cached   Call Provider
                                           → Cache Response
                                           → Return
```

### Similarity Matching

The cache uses cosine similarity to find matching prompts:

- **Exact Match**: 100% similarity → immediate cache hit
- **Semantic Match**: ≥92% similarity → cache hit
- **No Match**: <92% similarity → cache miss, call provider

### Cache Keys

Caches are scoped by:
- **Tenant ID** - Each tenant has isolated cache
- **Model** - Responses cached per model
- **Messages** - Full conversation context

## Cache Statistics

View cache performance in the Statistics page or via API:

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
  "evictions": 50,
  "cache_size": 500,
  "tokens_saved": 75000,
  "cost_saved_usd": 1.50,
  "cost_saved_inr": 125.25,
  "embeddings_indexed": 1500,
  "tenants_cached": 3
}
```

### Key Metrics

| Metric | Description |
|--------|-------------|
| `hits` | Number of requests served from cache |
| `misses` | Number of requests that required provider calls |
| `hit_rate` | Percentage of requests served from cache |
| `evictions` | Number of entries removed due to TTL or size limits |
| `cache_size` | Current number of entries in cache |
| `tokens_saved` | Estimated tokens saved from cache hits |
| `cost_saved_usd` | Estimated cost savings in USD |
| `cost_saved_inr` | Estimated cost savings in INR |

## Cache Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| TTL | 3600s (1 hour) | Time-to-live for cache entries |
| Max Size | 10,000 | Maximum entries per tenant |
| Similarity Threshold | 0.92 (92%) | Minimum similarity for cache hit |

### Customizing Configuration

Set via environment variables:

```bash
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=10000
CACHE_SIMILARITY_THRESHOLD=0.92
```

## Cache Management

### Clear All Cache

Via UI: Statistics → Cache tab → "Clear Cache" button

Via API:
```bash
DELETE /api/v1/admin/cache/clear
Authorization: Bearer YOUR_TOKEN
```

Response:
```json
{
  "message": "Cache cleared successfully"
}
```

### Invalidate Tenant Cache

The cache automatically invalidates when:
- TTL expires (default: 1 hour)
- Cache size limit is reached (oldest entries evicted)
- Manual clear is triggered

## Cost Savings Estimation

The system estimates savings based on model pricing:

| Model Family | Estimated Cost (per 1K tokens) |
|--------------|-------------------------------|
| GPT-4 | $0.03 |
| Claude | $0.015 |
| Other | $0.002 |

When a cache hit occurs:
1. Estimate tokens that would have been used
2. Calculate cost based on model
3. Add to cumulative savings

## Dashboard Integration

The Dashboard shows cache savings when available:

```
┌─────────────────────────────────────────┐
│ 💚 Prompt Cache Savings                 │
│                                         │
│ 16.7% cache hit rate • 75K tokens saved │
│                                         │
│                           ₹125.25       │
│                      Estimated savings  │
└─────────────────────────────────────────┘
```

## Redis Backend (Production)

For production deployments, configure Redis for persistent caching:

```bash
REDIS_URL=redis://localhost:6379
```

Benefits of Redis backend:
- Persistence across restarts
- Shared cache across multiple instances
- Better memory management

## Best Practices

### 1. Monitor Hit Rate

A healthy cache should have 15-30% hit rate. If lower:
- Users may be asking unique questions
- TTL may be too short
- Similarity threshold may be too high

### 2. Adjust Similarity Threshold

- **Higher (95%)**: Fewer false positives, fewer hits
- **Lower (85%)**: More hits, but may return less relevant cached responses

### 3. Set Appropriate TTL

- **Short TTL (15 min)**: For rapidly changing information
- **Long TTL (4 hours)**: For stable, factual information

### 4. Exclude Certain Requests

Some requests shouldn't be cached:
- Requests with `temperature > 0` (non-deterministic)
- Requests requiring real-time data
- Requests with user-specific context

## Limitations

1. **Streaming Responses** - Cached responses return as complete (non-streaming)
2. **Function Calling** - Function call responses are not cached
3. **Memory Usage** - Embeddings require memory; monitor usage
4. **First-call Latency** - First unique request has normal latency

## Troubleshooting

### Cache Not Working

1. Check if enabled:
```bash
echo $ENABLE_SEMANTIC_CACHE
```

2. Check cache stats:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/admin/cache/stats
```

### Low Hit Rate

1. Verify similar prompts are being sent
2. Check similarity threshold isn't too high
3. Verify TTL isn't too short

### High Memory Usage

1. Reduce `CACHE_MAX_SIZE`
2. Reduce TTL to evict entries faster
3. Use Redis backend instead of in-memory
