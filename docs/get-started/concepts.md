# Main concepts

Understand the core concepts that power AI Gateway.

---

## Architecture overview

```
┌─────────────────────────────────────────────────────────────┐
│                       AI Gateway                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Tenants  │  │ API Keys │  │Guardrails│  │  Router  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                       Providers                              │
│  ┌────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐            │
│  │ OpenAI │ │ Anthropic│ │ Google │ │  More   │            │
│  └────────┘ └──────────┘ └────────┘ └─────────┘            │
└─────────────────────────────────────────────────────────────┘
```

---

## Tenants

A **tenant** represents an organization or account in AI Gateway.

```python
# Each tenant has:
{
    "id": 1,
    "name": "Acme Corp",
    "email": "admin@acme.com",
    "rate_limit": 100,           # Requests per minute
    "monthly_budget": 1000.0,    # Cost limit
    "allowed_models": ["gpt-4", "claude-3"],
    "guardrail_profile_id": 1
}
```

### Key features

| Feature | Description |
|---------|-------------|
| **Isolation** | Each tenant's data is isolated |
| **Rate limits** | Per-tenant request limits |
| **Budgets** | Monthly/daily cost ceilings |
| **Model access** | Control which models are available |

---

## API Keys

**API keys** authenticate requests to the gateway.

```
sk-gw-Av0lUyrslJHxACCBMftOyZSijrbxJET-WJwXMR-fXuM
│     │
│     └── Unique identifier
└── Prefix (sk-gw-)
```

### Key capabilities

```python
# API keys can have:
{
    "name": "Production Key",
    "environment": "production",
    "rate_limit_override": 500,      # Override tenant limit
    "allowed_models_override": [...], # Restrict models
    "cost_limit_daily": 50.0,        # Daily spend limit
    "expires_at": "2025-12-31"       # Expiration date
}
```

!!! tip "Best practice"
    Create separate keys for different environments (dev, staging, prod) and applications.

---

## Guardrails

**Guardrails** protect your AI applications from security threats and ensure compliance.

### Input guardrails

Applied to user messages before sending to the AI provider:

| Guardrail | Description |
|-----------|-------------|
| **PII Detection** | Detects SSN, credit cards, emails, phones |
| **Prompt Injection** | Blocks "ignore instructions" attacks |
| **Jailbreak Detection** | Prevents safety bypass attempts |

### Output guardrails

Applied to AI responses before returning to users:

| Guardrail | Description |
|-----------|-------------|
| **PII Detection** | Redacts sensitive data in responses |
| **Content Moderation** | Filters inappropriate content |

### Example

```bash
# Input: "My SSN is 123-45-6789"
# After guardrails: "My SSN is [SSN_REDACTED]"
```

---

## Providers

**Providers** are the AI services that AI Gateway routes requests to.

### Supported providers

| Provider | Models | Status |
|----------|--------|--------|
| OpenAI | GPT-4, GPT-3.5, Embeddings | ✓ Active |
| Anthropic | Claude 3.5, Claude 3 | ✓ Active |
| Google | Gemini 2, Gemini 1.5 | ✓ Active |
| Azure OpenAI | GPT-4, GPT-3.5 | ✓ Active |
| AWS Bedrock | Claude, Titan | ✓ Active |
| Local vLLM | Custom models | ✓ Active |

---

## Router

The **router** intelligently directs requests to the best provider.

### Routing strategies

=== "Cost Optimized"

    Routes to the cheapest available model.

    ```
    Priority: gpt-4o-mini → claude-3-haiku → gpt-3.5-turbo
    ```

=== "Quality First"

    Routes to the highest quality model.

    ```
    Priority: gpt-4o → claude-3-opus → gemini-pro
    ```

=== "Balanced"

    Balances cost and quality.

    ```
    Priority: gpt-4o-mini → claude-3-sonnet → gpt-4
    ```

### Fallback & retry

```
Request → OpenAI (fail) → Anthropic (fail) → Google (success!)
              │                │
              └── Retry 3x ────┘
```

---

## Usage tracking

AI Gateway automatically tracks:

| Metric | Description |
|--------|-------------|
| **Tokens** | Input/output tokens per request |
| **Cost** | Calculated cost based on provider pricing |
| **Latency** | Response time per request |
| **Errors** | Failed requests and error types |

### Dashboard view

```
┌─────────────────────────────────────────────┐
│  Today's Usage                               │
├─────────────────────────────────────────────┤
│  Requests: 1,234    Tokens: 45,678          │
│  Cost: $12.34       Avg Latency: 234ms      │
└─────────────────────────────────────────────┘
```

---

## Next steps



-    **Tutorial**

    Build a complete application with AI Gateway.

    [ Tutorial](tutorial.md)

-    **API Reference**

    Explore all available endpoints.

    [ API Reference](../develop/api-reference/index.md)



