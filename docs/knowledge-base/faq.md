# Frequently Asked Questions

Common questions about AI Gateway.

---

## General

### What is AI Gateway?

AI Gateway is an enterprise-grade API gateway for AI/LLM services. It provides a unified interface for routing requests to multiple AI providers with built-in security, usage tracking, and cost management.

### Which AI providers are supported?

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3.5, Claude 3)
- Google (Gemini 2, Gemini 1.5)
- Azure OpenAI
- AWS Bedrock
- Local vLLM instances

### Is AI Gateway OpenAI-compatible?

Yes! AI Gateway implements the OpenAI API format. You can use the OpenAI SDK by simply changing the `base_url`:

```python
client = openai.OpenAI(
    api_key="sk-gw-your-key",
    base_url="http://localhost:8000/api/v1"
)
```

---

## Account & Access

### How do I reset my password? {#reset-password}

Currently, password reset is handled by your administrator. Contact your admin to reset your password, or use SSO if configured.

### How do I contact support? {#support}

- **GitHub Issues**: [Report bugs](https://github.com/your-org/ai-gateway/issues)
- **Discussions**: [Ask questions](https://github.com/your-org/ai-gateway/discussions)
- **Email**: support@your-org.com

### Where can I report a bug? {#report-bug}

Open an issue on our [GitHub repository](https://github.com/your-org/ai-gateway/issues) with:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, version)

---

## API Keys

### How do I create an API key?

1. Log in to the dashboard
2. Navigate to **API Keys**
3. Click **Create New Key**
4. Save the key securely (it's only shown once)

Or via API:
```bash
curl -X POST http://localhost:8000/api/v1/admin/api-keys \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "My Key"}'
```

### Can I set limits on API keys?

Yes! Each API key can have:
- Rate limit override
- Daily/monthly cost limits
- Allowed models restriction
- Expiration date

### What happens if my API key is compromised?

Immediately revoke the key in the dashboard or via API:
```bash
curl -X DELETE http://localhost:8000/api/v1/admin/api-keys/{key_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Billing & Usage

### How is usage calculated?

Usage is tracked per request:
- **Tokens**: Input + output tokens
- **Cost**: Based on provider pricing for the model used

### Can I set spending limits?

Yes, you can set:
- **Monthly budget** at the tenant level
- **Daily/monthly limits** per API key
- **Alerts** when thresholds are reached

### How do I export usage data?

Navigate to **Usage** in the dashboard and click **Export**, or use the API:
```bash
curl http://localhost:8000/api/v1/admin/usage/export \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Guardrails

### What guardrails are available?

- **PII Detection**: SSN, credit cards, emails, phones
- **Prompt Injection**: Blocks manipulation attempts
- **Jailbreak Detection**: Prevents safety bypasses
- **Content Moderation**: Filters inappropriate content

### Can I customize guardrails?

Yes, you can create custom policies combining different guardrails with specific configurations and actions (block, redact, warn).

### Do guardrails affect latency?

Guardrails add minimal latency (~5-10ms). For high-throughput applications, you can adjust policies or use async processing.
