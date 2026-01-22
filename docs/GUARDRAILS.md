# 🛡️ Guardrails Configuration Guide

AI Gateway includes comprehensive guardrails to protect against security threats, ensure compliance, and maintain content quality. This guide covers all available guardrails and how to configure them.

---

## Overview

Guardrails process both **input** (user prompts) and **output** (AI responses) to:

- Detect and redact sensitive information (PII)
- Block prompt injection and jailbreak attempts
- Enforce content policies
- Ensure compliance with regulations (BFSI, GDPR, etc.)

---

## Available Guardrails

### 1. PII Detection & Redaction

Detects and handles personally identifiable information.

| PII Type | Pattern | Example |
|----------|---------|---------|
| SSN | XXX-XX-XXXX | 123-45-6789 |
| Credit Card | 16-digit numbers | 4111-1111-1111-1111 |
| Email | email@domain.com | user@company.com |
| Phone | Various formats | (555) 123-4567 |
| Bank Account | Account numbers | 1234567890 |
| Date of Birth | Date patterns | 01/15/1990 |

**Actions:**
- `redact` - Replace with placeholder (default)
- `block` - Reject the request entirely
- `warn` - Allow but log warning

**API Configuration:**
```json
{
  "guardrail_id": "pii_detection",
  "enabled": true,
  "config": {
    "detect_types": ["ssn", "credit_card", "email", "phone"],
    "action": "redact",
    "redaction_placeholder": "[REDACTED]"
  }
}
```

### 2. Prompt Injection Detection

Blocks attempts to manipulate AI behavior through malicious prompts.

**Detected Patterns:**
- "Ignore previous instructions"
- "Forget your rules"
- "You are now DAN"
- Role manipulation attempts
- System prompt extraction

**Actions:**
- `block` - Reject request (recommended)
- `warn` - Allow but log

**API Configuration:**
```json
{
  "guardrail_id": "prompt_injection",
  "enabled": true,
  "config": {
    "sensitivity": "medium",
    "action": "block",
    "custom_patterns": [
      "ignore all previous",
      "disregard your training"
    ]
  }
}
```

### 3. Jailbreak Detection

Detects attempts to bypass AI safety measures.

**Detected Patterns:**
- Roleplay bypass attempts
- "Pretend you have no restrictions"
- Developer mode exploits
- Token manipulation

**API Configuration:**
```json
{
  "guardrail_id": "jailbreak",
  "enabled": true,
  "config": {
    "action": "block",
    "sensitivity": "high"
  }
}
```

### 4. Content Moderation

Filters inappropriate or harmful content.

**Categories:**
- Violence
- Adult content
- Hate speech
- Self-harm
- Illegal activities

**API Configuration:**
```json
{
  "guardrail_id": "content_moderation",
  "enabled": true,
  "config": {
    "blocked_categories": ["violence", "adult", "hate_speech"],
    "action": "block"
  }
}
```

### 5. Financial Advice Guard (BFSI)

Prevents unauthorized financial advice for banking/financial services.

**Detects:**
- Investment recommendations
- Stock tips
- Financial predictions
- Personalized financial advice

**API Configuration:**
```json
{
  "guardrail_id": "financial_advice",
  "enabled": true,
  "config": {
    "action": "block",
    "disclaimer_required": true
  }
}
```

### 6. Confidential Data Protection

Prevents disclosure of proprietary information.

**Protects:**
- Trade secrets
- Internal processes
- Confidential business information
- Proprietary algorithms

**API Configuration:**
```json
{
  "guardrail_id": "confidential_data",
  "enabled": true,
  "config": {
    "action": "block",
    "custom_terms": ["project apollo", "secret sauce"]
  }
}
```

---

## Guardrail Policies

Policies combine multiple guardrails into reusable configurations.

### Default Policy

```json
{
  "name": "default",
  "description": "Standard protection for general use",
  "guardrails": [
    {
      "id": "pii_detection",
      "enabled": true,
      "action": "redact"
    },
    {
      "id": "prompt_injection",
      "enabled": true,
      "action": "block"
    }
  ]
}
```

### Strict Policy

```json
{
  "name": "strict",
  "description": "Maximum protection - blocks on any detection",
  "guardrails": [
    {
      "id": "pii_detection",
      "enabled": true,
      "action": "block"
    },
    {
      "id": "prompt_injection",
      "enabled": true,
      "action": "block",
      "sensitivity": "high"
    },
    {
      "id": "jailbreak",
      "enabled": true,
      "action": "block"
    },
    {
      "id": "content_moderation",
      "enabled": true,
      "action": "block"
    }
  ]
}
```

### BFSI Compliance Policy

```json
{
  "name": "bfsi",
  "description": "Banking, Financial Services, Insurance compliance",
  "guardrails": [
    {
      "id": "pii_detection",
      "enabled": true,
      "action": "redact",
      "detect_types": ["ssn", "credit_card", "bank_account", "dob"]
    },
    {
      "id": "financial_advice",
      "enabled": true,
      "action": "block"
    },
    {
      "id": "confidential_data",
      "enabled": true,
      "action": "block"
    },
    {
      "id": "prompt_injection",
      "enabled": true,
      "action": "block"
    }
  ]
}
```

---

## API Reference

### List Available Guardrails

```bash
GET /api/v1/admin/guardrails
Authorization: Bearer YOUR_TOKEN
```

Response:
```json
{
  "guardrails": [
    {
      "id": "pii_detection",
      "name": "PII Detection",
      "description": "Detects and redacts PII",
      "actions": ["redact", "block", "warn"],
      "bfsi_relevant": true
    }
  ]
}
```

### Test Guardrails

```bash
POST /api/v1/admin/guardrails/test
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "text": "My SSN is 123-45-6789 and email is test@example.com",
  "policy": "default",
  "is_input": true
}
```

Response:
```json
{
  "original_text": "My SSN is 123-45-6789 and email is test@example.com",
  "processed_text": "My SSN is [SSN_REDACTED] and email is [EMAIL_REDACTED]",
  "blocked": false,
  "warnings": [],
  "triggered_guardrails": [
    {"type": "pii_detection", "detected_types": ["ssn", "email"]}
  ],
  "actions_taken": ["redacted_pii"]
}
```

### List Policies

```bash
GET /api/v1/admin/guardrails/policies
Authorization: Bearer YOUR_TOKEN
```

### Create Custom Policy

```bash
POST /api/v1/admin/guardrails/policies
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "custom-policy",
  "description": "Custom guardrail policy",
  "guardrails": [
    {
      "id": "pii_detection",
      "enabled": true,
      "config": {
        "action": "redact",
        "detect_types": ["ssn", "credit_card"]
      }
    }
  ]
}
```

---

## Integration with Chat Completions

Guardrails are automatically applied based on tenant/API key configuration.

### Per-Tenant Configuration

```bash
PATCH /api/v1/admin/tenants/{tenant_id}
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "guardrail_profile_id": 1
}
```

### Per-API-Key Configuration

```bash
POST /api/v1/admin/api-keys
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "Strict API Key",
  "guardrail_profile_id": 2
}
```

### Request-Level Override

```bash
POST /api/v1/chat/completions
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json

{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "Hello"}],
  "guardrail_policy": "strict"
}
```

---

## Best Practices

### 1. Start with Default Policy

Use the default policy initially and adjust based on your needs.

### 2. Test Before Deploying

Always test guardrail configurations with sample data:

```bash
curl -X POST /api/v1/admin/guardrails/test \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"text": "Test content", "policy": "your-policy", "is_input": true}'
```

### 3. Monitor Triggered Guardrails

Review audit logs to understand what's being blocked:

```bash
GET /api/v1/admin/audit-logs?action=guardrail_triggered
```

### 4. Use BFSI Policy for Financial Applications

If handling financial data, use the BFSI-compliant policy.

### 5. Layer Multiple Guardrails

Combine guardrails for defense in depth:

```json
{
  "guardrails": [
    {"id": "pii_detection", "action": "redact"},
    {"id": "prompt_injection", "action": "block"},
    {"id": "content_moderation", "action": "warn"}
  ]
}
```

---

## Troubleshooting

### False Positives

If legitimate content is being blocked:

1. Check which guardrail triggered
2. Adjust sensitivity settings
3. Add to allowlist if applicable
4. Use `warn` action instead of `block`

### Performance Impact

Guardrails add minimal latency (~5-10ms). For high-throughput applications:

1. Use simpler policies in hot paths
2. Enable caching for repeated patterns
3. Consider async processing for output guardrails

### Custom Patterns Not Working

Ensure regex patterns are properly escaped:

```json
{
  "custom_patterns": [
    "ignore\\s+previous",
    "secret\\s*project\\s*\\w+"
  ]
}
```

