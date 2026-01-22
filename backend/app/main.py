import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time

from backend.app.core.config import settings
from backend.app.core.rate_limit import rate_limiter
from backend.app.db.session import engine, Base
from backend.app.api.v1 import routes_chat, routes_admin, routes_users, routes_audit, routes_billing, routes_guardrails, routes_router, routes_providers, routes_organization, routes_external_guardrails, routes_load_balancer, routes_alerts, routes_budget
from backend.app.utils.metrics import get_metrics, ACTIVE_REQUESTS

from backend.app.db.models.tenant import Tenant
from backend.app.db.models.api_key import APIKey
from backend.app.db.models.usage_log import UsageLog
from backend.app.db.models.sso_config import SSOConfig
from backend.app.db.models.user import User
from backend.app.db.models.audit_log import AuditLog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Gateway...")
    
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    await rate_limiter.init()
    logger.info("Rate limiter initialized")
    
    if settings.ENABLE_TELEMETRY:
        from backend.app.telemetry import init_telemetry
        init_telemetry(
            service_name=settings.PROJECT_NAME,
            service_version=settings.VERSION,
            otlp_endpoint=settings.OTLP_ENDPOINT,
            enable_console_export=settings.TELEMETRY_CONSOLE_EXPORT
        )
        logger.info("OpenTelemetry initialized")
    
    if settings.ENABLE_SEMANTIC_CACHE:
        from backend.app.services.semantic_cache_service import semantic_cache
        await semantic_cache.init_redis()
        logger.info("Semantic cache initialized")
    
    # Initialize API key cache (PERFORMANCE OPTIMIZATION)
    from backend.app.core.api_key_cache import api_key_cache
    await api_key_cache.init_redis()
    logger.info("API key cache initialized")
    
    yield
    
    if settings.ENABLE_TELEMETRY:
        from backend.app.telemetry import shutdown_telemetry
        shutdown_telemetry()
    
    await rate_limiter.close()
    logger.info("AI Gateway shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise AI Gateway with multi-provider routing, guardrails, and usage tracking",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add performance monitoring middleware (OPTIMIZATION)
from backend.app.middleware.performance_monitor import PerformanceMonitorMiddleware
app.add_middleware(PerformanceMonitorMiddleware, slow_request_threshold_ms=100)

if settings.ENABLE_TELEMETRY:
    from backend.app.telemetry import TelemetryMiddleware
    app.add_middleware(TelemetryMiddleware)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(time.time()))
    start_time = time.time()
    
    ACTIVE_REQUESTS.inc()
    
    try:
        response = await call_next(request)
        
        latency = time.time() - start_time
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=int(latency * 1000)
        )
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{int(latency * 1000)}ms"
        
        return response
    finally:
        ACTIVE_REQUESTS.dec()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred"}
    )


app.include_router(
    routes_chat.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["AI Endpoints"]
)

app.include_router(
    routes_admin.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["Admin"]
)

app.include_router(
    routes_users.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["User Management"]
)

app.include_router(
    routes_audit.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["Audit Logs"]
)

app.include_router(
    routes_billing.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["Billing"]
)

app.include_router(
    routes_guardrails.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["Guardrails"]
)

app.include_router(
    routes_router.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["Router Configuration"]
)

app.include_router(
    routes_providers.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["Provider Configuration"]
)

app.include_router(
    routes_organization.router,
    prefix=f"{settings.API_V1_PREFIX}/admin/organization",
    tags=["Organization Management"]
)

app.include_router(
    routes_external_guardrails.router,
    prefix=f"{settings.API_V1_PREFIX}/admin/guardrails/external",
    tags=["External Guardrail Providers"]
)

app.include_router(
    routes_load_balancer.router,
    prefix=f"{settings.API_V1_PREFIX}/admin/router",
    tags=["Load Balancer & Circuit Breaker"]
)

app.include_router(
    routes_alerts.router,
    prefix=f"{settings.API_V1_PREFIX}/admin/alerts",
    tags=["Alerts & Notifications"]
)

app.include_router(
    routes_budget.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["Budget Management"]
)


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "docs": "/docs",
        "features": {
            "telemetry": settings.ENABLE_TELEMETRY,
            "semantic_cache": settings.ENABLE_SEMANTIC_CACHE,
            "content_routing": settings.ENABLE_CONTENT_ROUTING,
            "stream_inspection": settings.ENABLE_STREAM_INSPECTION,
            "load_balancing": True,
            "circuit_breaker": True,
            "request_transformation": True
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    return get_metrics()


@app.get("/api/v1/admin/features/status")
async def feature_status():
    features = {
        "telemetry": {
            "enabled": settings.ENABLE_TELEMETRY,
            "otlp_endpoint": settings.OTLP_ENDPOINT or "not configured"
        },
        "semantic_cache": {
            "enabled": settings.ENABLE_SEMANTIC_CACHE,
            "similarity_threshold": settings.SEMANTIC_CACHE_SIMILARITY_THRESHOLD,
            "ttl_seconds": settings.SEMANTIC_CACHE_TTL_SECONDS,
            "max_size": settings.SEMANTIC_CACHE_MAX_SIZE
        },
        "content_routing": {
            "enabled": settings.ENABLE_CONTENT_ROUTING
        },
        "stream_inspection": {
            "enabled": settings.ENABLE_STREAM_INSPECTION,
            "inspection_interval": settings.STREAM_INSPECTION_INTERVAL,
            "min_chars": settings.STREAM_INSPECTION_MIN_CHARS
        }
    }
    
    if settings.ENABLE_SEMANTIC_CACHE:
        from backend.app.services.semantic_cache_service import semantic_cache
        features["semantic_cache"]["stats"] = semantic_cache.get_stats()
    
    if settings.ENABLE_CONTENT_ROUTING:
        from backend.app.services.content_routing_service import content_routing_service
        features["content_routing"]["stats"] = content_routing_service.get_routing_stats()
    
    if settings.ENABLE_STREAM_INSPECTION:
        from backend.app.services.stream_inspection_service import stream_inspection_service
        features["stream_inspection"]["stats"] = stream_inspection_service.get_stats()
    
    # Add load balancer and circuit breaker stats
    from backend.app.services.load_balancer import load_balancer
    from backend.app.services.circuit_breaker import circuit_breaker_manager
    
    features["load_balancing"] = {
        "enabled": True,
        "stats": load_balancer.get_all_stats()
    }
    
    features["circuit_breaker"] = {
        "enabled": True,
        "unhealthy_providers": circuit_breaker_manager.get_unhealthy_providers(),
        "breaker_count": len(circuit_breaker_manager.get_all_metrics())
    }
    
    return features
