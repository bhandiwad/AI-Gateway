# Guardrails API

Endpoints for managing and testing guardrails.

---

## List Guardrails {#list}

```http
GET /api/v1/admin/guardrails
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
```json
{
  "guardrails": [
    {
      "id": "pii_detection",
      "name": "PII Detection",
      "description": "Detects and redacts personally identifiable information",
      "actions": ["redact", "block", "warn"],
      "bfsi_relevant": true
    },
    {
      "id": "prompt_injection",
      "name": "Prompt Injection Detection",
      "description": "Blocks prompt manipulation attempts",
      "actions": ["block", "warn"],
      "bfsi_relevant": false
    }
  ]
}
```

---

## Test Guardrails {#test}

```http
POST /api/v1/admin/guardrails/test
Authorization: Bearer YOUR_TOKEN
```

**Request:**
```json
{
  "text": "My SSN is 123-45-6789 and email is test@example.com",
  "policy": "default",
  "is_input": true
}
```

**Response (200):**
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

---

## List Policies {#policies}

```http
GET /api/v1/admin/guardrails/policies
Authorization: Bearer YOUR_TOKEN
```

**Response (200):**
```json
{
  "policies": [
    {
      "name": "default",
      "description": "Standard protection",
      "guardrails": ["pii_detection", "prompt_injection"]
    },
    {
      "name": "strict",
      "description": "Maximum protection",
      "guardrails": ["pii_detection", "prompt_injection", "jailbreak", "content_moderation"]
    },
    {
      "name": "bfsi",
      "description": "Banking/Financial compliance",
      "guardrails": ["pii_detection", "financial_advice", "confidential_data"]
    }
  ]
}
```

---

## BFSI Guardrails

```http
GET /api/v1/admin/guardrails/bfsi
Authorization: Bearer YOUR_TOKEN
```

Returns guardrails specific to Banking, Financial Services, and Insurance compliance.
