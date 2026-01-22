# Concepts

Deep dive into the core features and concepts of AI Gateway.

---



-    **[Guardrails](guardrails.md)**

    ---

    Protect your AI applications with PII detection, prompt injection blocking, and content moderation.

-    **[Routing](routing.md)**

    ---

    Multi-provider routing with strategies, fallbacks, and load balancing.

-    **[SSO](sso.md)**

    ---

    Single sign-on integration with Google, Microsoft, Okta, and other OIDC providers.

-    **[Rate Limiting](rate-limiting.md)**

    ---

    Control request rates per tenant, user, and API key.

-    **[Configuration](configuration.md)**

    ---

    Complete reference for all environment variables and settings.



---

## Overview

AI Gateway is built around several key concepts that work together:

### Request flow

```
Request → Auth → Rate Limit → Input Guardrails → Router → Provider → Output Guardrails → Response
```

### Core components

| Component | Purpose |
|-----------|---------|
| **Tenants** | Multi-tenant isolation, budgets, limits |
| **API Keys** | Request authentication, per-key limits |
| **Guardrails** | Security processing (PII, injection) |
| **Router** | Provider selection, fallbacks |
| **Providers** | OpenAI, Anthropic, Google, etc. |

---

## Next steps

Choose a concept to explore:

- [Guardrails](guardrails.md) - Security and compliance
- [Routing](routing.md) - Multi-provider strategies
- [SSO](sso.md) - Enterprise authentication
- [Configuration](configuration.md) - Environment setup

