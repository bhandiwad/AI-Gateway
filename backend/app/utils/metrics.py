from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

REQUEST_COUNT = Counter(
    'ai_gateway_requests_total',
    'Total number of requests',
    ['endpoint', 'model', 'provider', 'status']
)

TOKEN_COUNT = Counter(
    'ai_gateway_tokens_total',
    'Total number of tokens processed',
    ['type', 'model', 'provider']
)

REQUEST_LATENCY = Histogram(
    'ai_gateway_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint', 'model'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

COST_COUNTER = Counter(
    'ai_gateway_cost_dollars_total',
    'Total cost in dollars',
    ['model', 'provider', 'tenant_id']
)

RATE_LIMIT_HITS = Counter(
    'ai_gateway_rate_limit_hits_total',
    'Number of rate limit hits',
    ['tenant_id']
)

GUARDRAIL_TRIGGERS = Counter(
    'ai_gateway_guardrail_triggers_total',
    'Number of guardrail triggers',
    ['rule', 'action']
)

ACTIVE_REQUESTS = Gauge(
    'ai_gateway_active_requests',
    'Number of active requests'
)

TENANT_BUDGET_USAGE = Gauge(
    'ai_gateway_tenant_budget_usage_ratio',
    'Tenant budget usage ratio',
    ['tenant_id']
)


def record_request(
    endpoint: str,
    model: str,
    provider: str,
    status: str,
    latency_seconds: float,
    prompt_tokens: int,
    completion_tokens: int,
    cost: float,
    tenant_id: str
):
    REQUEST_COUNT.labels(
        endpoint=endpoint,
        model=model,
        provider=provider,
        status=status
    ).inc()
    
    REQUEST_LATENCY.labels(
        endpoint=endpoint,
        model=model
    ).observe(latency_seconds)
    
    TOKEN_COUNT.labels(type='prompt', model=model, provider=provider).inc(prompt_tokens)
    TOKEN_COUNT.labels(type='completion', model=model, provider=provider).inc(completion_tokens)
    
    COST_COUNTER.labels(
        model=model,
        provider=provider,
        tenant_id=tenant_id
    ).inc(cost)


def record_rate_limit_hit(tenant_id: str):
    RATE_LIMIT_HITS.labels(tenant_id=tenant_id).inc()


def record_guardrail_trigger(rule: str, action: str):
    GUARDRAIL_TRIGGERS.labels(rule=rule, action=action).inc()


def get_metrics() -> Response:
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
