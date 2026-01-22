# Get started

Welcome to AI Gateway! This section will help you get up and running quickly.

| Guide | Description |
|-------|-------------|
| **[Installation](installation.md)** | Install AI Gateway using Docker or set up local development. |
| **[Quickstart](quickstart.md)** | Make your first API call in under 5 minutes. |
| **[Main Concepts](concepts.md)** | Understand tenants, API keys, providers, guardrails, and routing. |

---

## Prerequisites

Before you begin, make sure you have:

| Requirement | Version | Notes |
|-------------|---------|-------|
| Docker | 24.0+ | For containerized deployment |
| Docker Compose | 2.20+ | For multi-service orchestration |
| Python | 3.11+ | For local development (optional) |
| Node.js | 18+ | For frontend development (optional) |

You'll also need at least one AI provider API key:

- **OpenAI**: Get your key at [platform.openai.com](https://platform.openai.com)
- **Anthropic**: Get your key at [console.anthropic.com](https://console.anthropic.com)
- **Google AI**: Get your key at [makersuite.google.com](https://makersuite.google.com)

---

## Quick install

```bash
# Clone the repository
git clone https://github.com/your-org/ai-gateway.git
cd ai-gateway

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start AI Gateway
docker-compose up -d
```

**That's it!** AI Gateway is now running at:
- **Dashboard**: http://localhost
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Next steps

- **Ready to dive in?** Follow the [Quickstart guide](quickstart.md) to make your first API call.
- **Want to learn more?** Read about [Main concepts](concepts.md) to understand how AI Gateway works.
- **Ready to build?** Check out the [API Reference](../develop/api-reference/index.md) for complete documentation.
