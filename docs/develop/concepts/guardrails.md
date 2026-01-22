# Guardrails

Guardrails protect your AI applications from security threats and ensure compliance.

---

## Overview

AI Gateway processes both **input** (user prompts) and **output** (AI responses) through configurable guardrails:

```
User Input → [Input Guardrails] → AI Provider → [Output Guardrails] → Response
                    │                                    │
                    ├── PII Detection                   ├── PII Detection
                    ├── Prompt Injection                └── Content Moderation
                    └── Jailbreak Detection
```

---

## Available guardrails

### PII Detection

Detects and handles personally identifiable information.

| Type | Examples |
|------|----------|
| SSN | 123-45-6789 |
| Credit Card | 4111-1111-1111-1111 |
| Email | user@company.com |
| Phone | (555) 123-4567 |
| Bank Account | Account numbers |

**Actions:**

=== "Redact"
    ```
    Input:  "My SSN is 123-45-6789"
    Output: "My SSN is [SSN_REDACTED]"
    ```

=== "Block"
    ```
    HTTP 400: Request blocked - PII detected
    ```

=== "Warn"
    ```
    Request proceeds, warning logged
    ```

### Prompt Injection

Blocks attempts to manipulate AI behavior.

**Detected patterns:**
- "Ignore previous instructions"
- "Forget your rules"
- "You are now DAN"
- System prompt extraction attempts

### Jailbreak Detection

Prevents AI safety bypass attempts.

**Detected patterns:**
- Roleplay bypass attempts
- "Pretend you have no restrictions"
- Developer mode exploits

---

## Policies

Policies combine multiple guardrails into reusable configurations.

### Default policy

```json
{
  "name": "default",
  "guardrails": [
    {"id": "pii_detection", "action": "redact"},
    {"id": "prompt_injection", "action": "block"}
  ]
}
```

### Strict policy

```json
{
  "name": "strict",
  "guardrails": [
    {"id": "pii_detection", "action": "block"},
    {"id": "prompt_injection", "action": "block"},
    {"id": "jailbreak", "action": "block"},
    {"id": "content_moderation", "action": "block"}
  ]
}
```

### BFSI policy

For banking and financial services:

```json
{
  "name": "bfsi",
  "guardrails": [
    {"id": "pii_detection", "action": "redact"},
    {"id": "financial_advice", "action": "block"},
    {"id": "confidential_data", "action": "block"}
  ]
}
```

---

## Testing guardrails

Use the test endpoint to verify guardrail behavior:

```bash
curl -X POST http://localhost:8000/api/v1/admin/guardrails/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "My SSN is 123-45-6789",
    "policy": "default",
    "is_input": true
  }'
```

**Response:**

```json
{
  "original_text": "My SSN is 123-45-6789",
  "processed_text": "My SSN is [SSN_REDACTED]",
  "blocked": false,
  "triggered_guardrails": [
    {"type": "pii_detection", "detected_types": ["ssn"]}
  ],
  "actions_taken": ["redacted_pii"]
}
```

---

## Configuration

### Per-tenant

```bash
PATCH /api/v1/admin/tenants/{id}
{
  "guardrail_profile_id": 1
}
```

### Per-API key

```bash
POST /api/v1/admin/api-keys
{
  "name": "Strict Key",
  "guardrail_profile_id": 2
}
```

---

## Best practices

!!! tip "Start with default policy"
    Use the default policy initially and adjust based on your needs.

!!! tip "Test before deploying"
    Always test guardrail configurations with sample data.

!!! tip "Monitor triggered guardrails"
    Review audit logs to understand what's being blocked.

!!! warning "Don't rely solely on guardrails"
    Guardrails are one layer of defense. Implement defense in depth.

