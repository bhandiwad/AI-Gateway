# Error Handling in AI Gateway

## Overview

The AI Gateway provides comprehensive error handling with:
- **Categorized errors** for better client understanding
- **User-friendly messages** (not technical stack traces)
- **Suggested actions** for resolution
- **Retry guidance** with timing recommendations
- **Quota/cost limit enforcement** before processing requests

---

## Error Categories

### 1. Authentication Errors (`401 Unauthorized`)

**When it happens:**
- Invalid or expired API key
- Missing authorization header
- Provider API key is invalid

**User Message:**
> "Authentication failed. Please check your API key."

**Suggested Action:**
- Verify API key is correct and active
- Check if key has expired
- Regenerate API key if compromised

---

### 2. Cost Limit Errors (`402 Payment Required`)

**When it happens:**
- API key daily/monthly cost limit exceeded
- User monthly budget exceeded
- Department/team budget exceeded
- Tenant (organization) budget exceeded

**User Messages:**

**API Key Limit:**
> "Daily cost limit exceeded for this API key. Limit: $50.00, Current spend: $52.34. Limit resets at midnight UTC."

**User Budget:**
> "Your monthly budget has been exceeded. Budget: $100.00, Current spend: $105.67. Please contact your administrator."

**Department Budget:**
> "Department monthly budget has been exceeded. Budget: $1000.00, Current spend: $1050.23. Contact your department manager."

**Tenant Budget:**
> "Organization monthly budget has been exceeded. Budget: $5000.00, Current spend: $5123.45. Contact support."

**Suggested Actions:**
- Wait for limit reset (daily limits)
- Contact administrator to increase budget
- Upgrade to higher tier
- Review usage patterns to optimize costs

**Check Limits Before Requests:**
```bash
# Get remaining budget
curl http://localhost:8000/api/v1/usage/limits \
  -H "Authorization: Bearer $API_KEY"

# Response:
{
  "api_key_daily_remaining": 25.50,
  "api_key_monthly_remaining": 150.00,
  "tenant_monthly_remaining": 2500.00
}
```

---

### 3. Rate Limit Errors (`429 Too Many Requests`)

**When it happens:**
- Gateway rate limit exceeded (tenant/API key level)
- Provider rate limit exceeded (OpenAI, Anthropic, etc.)

**User Messages:**

**Gateway Rate Limit:**
> "You have exceeded the rate limit. Please wait before making more requests."

**Provider Rate Limit:**
> "The AI provider's rate limit has been exceeded. Please try again in a moment."

**Suggested Actions:**
- Wait 60 seconds (gateway) or 30 seconds (provider)
- Upgrade to higher rate limit tier
- Implement exponential backoff in client

**Response Headers:**
```
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1702345678
```

---

### 4. Provider Quota Errors (`429 Too Many Requests`)

**When it happens:**
- OpenAI account has exceeded quota
- Provider billing hard limit reached
- No remaining credits with provider

**User Message:**
> "The AI provider has reached its usage quota. Please contact support to increase limits."

**Suggested Action:**
> "Add payment method or increase quota limits in provider dashboard"

**Technical Details:**
Provider errors like:
- "You exceeded your current quota"
- "insufficient_quota"
- "billing hard limit has been reached"

---

### 5. Provider Payment Errors (`402 Payment Required`)

**When it happens:**
- Provider credit card declined
- Provider account suspended for payment
- Payment method expired

**User Message:**
> "The AI provider account has a payment issue. Please update payment information."

**Suggested Action:**
> "Update payment method in provider dashboard"

**Technical Details:**
Provider errors like:
- "payment required"
- "billing issue"
- "credit card declined"
- "account suspended due to payment"

---

### 6. Circuit Breaker Errors (`503 Service Unavailable`)

**When it happens:**
- Provider has failed 5+ times in 60 seconds
- Circuit breaker is in OPEN state
- Provider marked as unhealthy

**User Message:**
> "The AI provider is currently unavailable due to repeated failures. Trying alternative providers."

**Suggested Action:**
> "Wait 30 seconds for automatic recovery or try a different model"

**Response Headers:**
```
Retry-After: 30
X-Circuit-State: OPEN
X-Provider-Status: unhealthy
```

**Automatic Behavior:**
- Gateway automatically tries fallback providers
- Circuit auto-recovers after 30 seconds
- Enters HALF_OPEN state for testing
- Closes if 2 consecutive requests succeed

---

### 7. Guardrail Violation Errors (`400 Bad Request`)

**When it happens:**
- Content blocked by safety guardrails
- PII detected in input
- Toxicity/hate speech detected
- Prompt injection attempt detected
- Provider content policy violated

**User Message:**
> "The request was blocked by content safety guardrails."

**Details:**
```json
{
  "error": {
    "type": "guardrail_violation",
    "message": "The request was blocked by content safety guardrails.",
    "details": {
      "triggered_rule": "pii_detection",
      "category": "personal_information"
    },
    "suggested_action": "Modify the request to comply with safety policies"
  }
}
```

**Suggested Actions:**
- Remove PII (email, phone, SSN, credit cards)
- Rephrase to avoid toxic content
- Review content policy guidelines

---

### 8. Provider Unavailable Errors (`503 Service Unavailable`)

**When it happens:**
- Provider API is down (503, 504)
- Temporary service outage
- Network timeout

**User Message:**
> "The AI provider is temporarily unavailable. The request will be retried automatically."

**Suggested Action:**
> "Wait for automatic retry or try again later"

**Response Headers:**
```
Retry-After: 10
X-Fallback-Attempted: true
```

**Automatic Behavior:**
- Gateway automatically retries with exponential backoff
- Tries fallback providers in order
- Logs incident for monitoring

---

### 9. Model Not Found Errors (`400 Bad Request`)

**When it happens:**
- Requested model doesn't exist
- Model not available in current provider plan
- Model deprecated or removed

**User Message:**
> "The requested AI model is not available with your current provider plan."

**Suggested Action:**
> "Check available models or upgrade provider plan"

**Get Available Models:**
```bash
curl http://localhost:8000/api/v1/models \
  -H "Authorization: Bearer $API_KEY"
```

---

## Error Response Format

All errors follow a consistent structure:

```json
{
  "error": {
    "type": "cost_limit",
    "message": "Daily cost limit exceeded for this API key. Limit: $50.00, Current spend: $52.34",
    "details": {
      "limit": 50.00,
      "current_spend": 52.34,
      "reset_at": "2024-12-05T00:00:00Z"
    },
    "retry_after_seconds": null,
    "suggested_action": "Wait for limit reset at midnight UTC or contact administrator"
  }
}
```

### Fields:
- **type**: Error category (see categories above)
- **message**: User-friendly description
- **details**: Additional context (varies by error type)
- **retry_after_seconds**: Seconds to wait before retry (if applicable)
- **suggested_action**: What the user should do

---

## Monitoring & Alerts

### Error Metrics Tracked:

```python
# Prometheus metrics
ai_gateway_errors_total{category="provider_quota", tenant_id="123"}
ai_gateway_cost_limit_exceeded_total{level="api_key", tenant_id="123"}
ai_gateway_circuit_breaker_open{provider="openai"}
```

### Dashboard Integration:

The frontend dashboard shows:
- **Cost Limit Warnings**: When 90% of budget is consumed
- **Circuit Breaker Status**: Real-time health of all providers
- **Error Rate Trends**: By category over time
- **Quota Usage**: Daily/monthly spend tracking

---

## Client Best Practices

### 1. Handle Retry-After Header

```python
import requests
import time

response = requests.post(...)
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    print(f"Rate limited. Waiting {retry_after} seconds...")
    time.sleep(retry_after)
    # Retry request
```

### 2. Implement Exponential Backoff

```python
import time
import random

def make_request_with_backoff(max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(...)
            if response.status_code == 200:
                return response
            elif response.status_code in [429, 503]:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
            else:
                break  # Don't retry other errors
        except Exception as e:
            if attempt == max_retries - 1:
                raise
    return None
```

### 3. Monitor Budget Usage

```python
# Check remaining budget before expensive operations
limits = requests.get(
    "http://gateway/api/v1/usage/limits",
    headers={"Authorization": f"Bearer {api_key}"}
).json()

if limits["api_key_daily_remaining"] < 5.0:
    print("Warning: Less than $5 remaining in daily budget")
```

### 4. Handle Circuit Breaker Gracefully

```python
response = requests.post(...)
if response.status_code == 503:
    error = response.json().get("error", {})
    if error.get("type") == "circuit_breaker":
        # Provider is down, use alternative model
        response = requests.post(..., json={"model": "alternative-model"})
```

---

## Admin Actions

### View Error Statistics:

```bash
# Get error breakdown
curl http://localhost:8000/api/v1/admin/errors/stats \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Response:
{
  "last_24h": {
    "provider_quota": 15,
    "cost_limit": 8,
    "rate_limit": 3,
    "circuit_breaker": 12
  }
}
```

### Manage Circuit Breakers:

```bash
# View all circuit breakers
curl http://localhost:8000/api/v1/admin/router/circuit-breakers \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Force close a stuck circuit
curl -X POST http://localhost:8000/api/v1/admin/router/circuit-breakers/openai/force-close \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Adjust Cost Limits:

```bash
# Update API key daily limit
curl -X PUT http://localhost:8000/api/v1/admin/api-keys/{key_id} \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"cost_limit_daily": 100.00}'

# Update department budget
curl -X PUT http://localhost:8000/api/v1/admin/organization/departments/{dept_id} \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"budget_monthly": 5000.00}'
```

---

## Summary

The AI Gateway provides enterprise-grade error handling with:

✅ **10+ error categories** for precise diagnosis  
✅ **User-friendly messages** (no technical jargon)  
✅ **Actionable suggestions** for every error  
✅ **Automatic retries** for transient failures  
✅ **Circuit breakers** prevent cascading failures  
✅ **Cost limit enforcement** before processing  
✅ **Detailed monitoring** via Prometheus metrics  
✅ **Real-time dashboards** for admins  

All errors are logged, tracked, and available in audit logs for compliance and debugging.
