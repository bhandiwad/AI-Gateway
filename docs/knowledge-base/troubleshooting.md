# Troubleshooting

Solutions for common issues with AI Gateway.

---

## Authentication Errors

### 401 Unauthorized {#401-unauthorized}

**Cause**: Invalid or missing authentication token/API key.

**Solutions**:
1. Verify your API key is correct and active
2. Check the Authorization header format: `Bearer YOUR_KEY`
3. Ensure the key hasn't expired
4. Confirm the key has required permissions

```bash
# Test your API key
curl -I http://localhost:8000/api/v1/admin/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 403 Forbidden

**Cause**: Valid authentication but insufficient permissions.

**Solutions**:
1. Check your role has the required permissions
2. Contact your admin to update permissions
3. Use an API key with appropriate access

---

## Connection Issues

### Request Timeout {#timeout}

**Cause**: Request took too long to complete.

**Solutions**:
1. Check provider health: `GET /api/v1/admin/router/health`
2. Reduce `max_tokens` in your request
3. Enable fallback to alternative providers
4. Check network connectivity to providers

```bash
# Check provider health
curl http://localhost:8000/api/v1/admin/router/health \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Connection Refused

**Cause**: AI Gateway service not running or unreachable.

**Solutions**:
1. Verify the service is running: `docker-compose ps`
2. Check the correct port (default: 8000)
3. Verify firewall rules allow the connection

---

## Rate Limiting

### 429 Too Many Requests {#rate-limit}

**Cause**: Exceeded rate limit for your tenant or API key.

**Solutions**:
1. Check your current rate limit in the dashboard
2. Implement exponential backoff in your client
3. Request a rate limit increase from your admin
4. Distribute requests across multiple API keys

**Response headers to check**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067200
```

---

## Provider Errors

### Provider Unavailable

**Cause**: AI provider (OpenAI, Anthropic, etc.) is down or unreachable.

**Solutions**:
1. Check provider status pages
2. Enable fallback routing to alternative providers
3. Circuit breaker will auto-recover when provider is healthy

### Model Not Found

**Cause**: Requested model doesn't exist or isn't configured.

**Solutions**:
1. Check available models: `GET /api/v1/admin/models`
2. Verify model name spelling
3. Ensure the provider for that model is configured

---

## Guardrail Issues

### Request Blocked by Guardrails

**Cause**: Input or output triggered a guardrail policy.

**Solutions**:
1. Check which guardrail was triggered in the response
2. Review your guardrail policy settings
3. Test with the guardrails test endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/admin/guardrails/test \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"text": "your text", "policy": "default"}'
```

---

## Database Issues

### Database Connection Failed

**Cause**: PostgreSQL not running or connection string incorrect.

**Solutions**:
1. Verify PostgreSQL is running: `docker-compose ps postgres`
2. Check DATABASE_URL environment variable
3. Test connection: `docker-compose exec postgres psql -U postgres`

### Migration Errors

**Cause**: Database schema out of sync.

**Solutions**:
1. Run migrations manually
2. Check for pending migrations
3. Backup and recreate database if needed

---

## Performance Issues

### Slow Response Times

**Cause**: Various factors can affect latency.

**Solutions**:
1. Enable semantic caching for repeated queries
2. Check provider latency in health endpoint
3. Use faster models (e.g., gpt-4o-mini vs gpt-4)
4. Review database connection pool settings

### High Memory Usage

**Cause**: Too many concurrent connections or large responses.

**Solutions**:
1. Increase container memory limits
2. Reduce connection pool size
3. Enable streaming for large responses

---

## Getting More Help

If you can't resolve your issue:

1. Check the [FAQ](faq.md)
2. Search [GitHub Issues](https://github.com/your-org/ai-gateway/issues)
3. Ask in [Discussions](https://github.com/your-org/ai-gateway/discussions)
4. Contact support@your-org.com
