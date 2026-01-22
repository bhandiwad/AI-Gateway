# Performance Optimization Quick Start

## Step 1: Apply Database Indexes (CRITICAL - 5 minutes)

### For PostgreSQL:
```bash
# From the AI-Gateway directory
psql -U your_username -d your_database_name -f backend/scripts/add_performance_indexes.sql
```

### For SQLite (Development):
```bash
sqlite3 your_database.db < backend/scripts/add_performance_indexes_sqlite.sql
```

Note: SQLite doesn't support CONCURRENTLY, but indexes are still beneficial.

## Step 2: Verify Indexes Were Created

```sql
-- PostgreSQL
SELECT indexname, tablename 
FROM pg_indexes 
WHERE indexname LIKE 'idx_%' 
ORDER BY tablename, indexname;

-- SQLite  
.indexes
```

You should see indexes like:
- idx_api_keys_hash_active
- idx_guardrail_profiles_tenant_active
- idx_routing_policies_tenant_active
- etc.

## Step 3: Restart Application

All code optimizations are already in place. Just restart:

```bash
# Docker
docker-compose restart backend

# Local development
cd backend
uvicorn app.main:app --reload
```

## Step 4: Test Performance

```bash
# Make a test request and check latency
curl -w "\nTime: %{time_total}s\n" \
  -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

Expected result: **<100ms total time** (most is LLM response, gateway overhead <10ms)

## Expected Performance Improvements

| Metric | Before | After | 
|--------|--------|-------|
| Gateway Latency | 50-150ms | <10ms |
| DB Queries/Request | 7-10 | 1-2 |
| Throughput | 200 RPS | 2000+ RPS |

## Monitoring

Check logs for performance metrics:
```bash
# See latencies
tail -f logs/gateway.log | grep latency_ms

# See slow requests (>100ms)
tail -f logs/gateway.log | grep slow_request

# Check cache hits
tail -f logs/gateway.log | grep api_key_cache
```

## Troubleshooting

**Issue**: Indexes not created  
**Solution**: Check database permissions, user needs CREATE INDEX privilege

**Issue**: High memory usage  
**Solution**: API key cache uses ~50-100MB, this is normal. Reduce `max_local_size` in api_key_cache.py if needed

**Issue**: Still slow after optimizations  
**Solution**: Check database connection pool usage, may need to increase further

## Production Checklist

- [ ] Database indexes applied
- [ ] Application restarted
- [ ] Latency verified (<10ms gateway overhead)
- [ ] Monitoring dashboards updated
- [ ] Alert thresholds adjusted (P99 <50ms)
- [ ] Load testing completed
