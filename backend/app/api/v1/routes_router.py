from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import yaml
import os

from backend.app.db.session import get_db
from backend.app.core.security import get_current_user
from backend.app.core.permissions import Permission, RequirePermission
from backend.app.services.router_service import router_service
from backend.app.db.models.usage_log import UsageLog

router = APIRouter()

class ProviderStatus(BaseModel):
    name: str
    type: str
    is_active: bool
    priority: int
    models: List[str]
    status: str = "active"

class RoutingStrategy(BaseModel):
    name: str
    description: str
    priority_order: List[str]
    enabled: bool = False

class FallbackConfig(BaseModel):
    enabled: bool
    max_retries: int
    fallback_order: List[str]

class RateLimitTier(BaseModel):
    name: str
    requests_per_minute: int
    tokens_per_minute: int

class RouterConfig(BaseModel):
    default_provider: str
    default_model: str
    strategies: List[RoutingStrategy]
    fallback: FallbackConfig
    rate_limit_tiers: List[RateLimitTier]
    load_balancing_enabled: bool
    caching_enabled: bool

class ProviderHealthCheck(BaseModel):
    provider: str
    status: str
    latency_ms: Optional[float]
    error: Optional[str]


def load_providers_config():
    config_path = os.path.join(os.path.dirname(__file__), '../../..', 'configs', 'providers.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception:
        return {"providers": []}


def load_routing_config():
    config_path = os.path.join(os.path.dirname(__file__), '../../..', 'configs', 'routing_rules.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception:
        return {"routing": {}}


@router.get("/router/providers")
async def get_providers(
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW)),
    db: Session = Depends(get_db)
):
    """Get all configured providers with their status"""
    config = load_providers_config()
    providers = []
    
    for p in config.get("providers", []):
        has_key = False
        if p.get("api_key_env"):
            has_key = bool(os.environ.get(p["api_key_env"]))
        
        status = "active" if p.get("is_active", False) and has_key else "inactive"
        if p.get("is_active", False) and not has_key:
            status = "no_api_key"
        
        providers.append({
            "name": p.get("name"),
            "type": p.get("type"),
            "is_active": p.get("is_active", False),
            "priority": p.get("priority", 99),
            "models": p.get("models", []),
            "status": status,
            "has_api_key": has_key,
            "config": p.get("config", {})
        })
    
    mock_provider = {
        "name": "mock",
        "type": "mock",
        "is_active": True,
        "priority": 100,
        "models": ["mock-gpt-4", "mock-claude"],
        "status": "active",
        "has_api_key": True,
        "config": {"description": "Mock provider for testing"}
    }
    providers.append(mock_provider)
    
    return {"providers": sorted(providers, key=lambda x: x["priority"])}


@router.get("/router/config")
async def get_router_config(
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW)),
    db: Session = Depends(get_db)
):
    """Get current routing configuration"""
    config = load_routing_config()
    routing = config.get("routing", {})
    
    strategies = []
    for s in routing.get("strategies", []):
        strategies.append({
            "name": s.get("name"),
            "description": s.get("description", ""),
            "priority_order": s.get("priority_order", []),
            "enabled": s.get("name") == "balanced"
        })
    
    fallback = routing.get("fallback", {})
    rate_limits = routing.get("rate_limits", {})
    
    tiers = []
    for tier_name, tier_config in rate_limits.get("tiers", {}).items():
        tiers.append({
            "name": tier_name,
            "requests_per_minute": tier_config.get("requests_per_minute", 100),
            "tokens_per_minute": tier_config.get("tokens_per_minute", 100000)
        })
    
    return {
        "default_provider": routing.get("default_provider", "openai"),
        "default_model": routing.get("default_model", "gpt-4o-mini"),
        "strategies": strategies,
        "fallback": {
            "enabled": fallback.get("enabled", True),
            "max_retries": fallback.get("max_retries", 2),
            "fallback_order": fallback.get("fallback_order", [])
        },
        "rate_limit_tiers": tiers,
        "load_balancing": routing.get("load_balancing", {}),
        "caching": routing.get("caching", {}),
        "model_aliases": routing.get("model_aliases", {})
    }


@router.get("/router/fallback-chain")
async def get_fallback_chain(
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW)),
    db: Session = Depends(get_db)
):
    """Get the current fallback provider chain"""
    config = load_routing_config()
    routing = config.get("routing", {})
    fallback = routing.get("fallback", {})
    
    providers_config = load_providers_config()
    provider_details = {p["name"]: p for p in providers_config.get("providers", [])}
    
    chain = []
    for provider_name in fallback.get("fallback_order", []):
        provider = provider_details.get(provider_name, {})
        chain.append({
            "name": provider_name,
            "is_active": provider.get("is_active", False),
            "priority": provider.get("priority", 99),
            "type": provider.get("type", "unknown")
        })
    
    return {
        "enabled": fallback.get("enabled", True),
        "max_retries": fallback.get("max_retries", 2),
        "chain": chain
    }


@router.post("/router/health-check")
async def check_provider_health(
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW)),
    db: Session = Depends(get_db)
):
    """Check health status of all providers"""
    results = []
    
    models = router_service.get_available_models()
    providers_seen = set()
    
    for model in models:
        provider = model.get("provider", "unknown")
        if provider in providers_seen:
            continue
        providers_seen.add(provider)
        
        if provider == "mock":
            results.append({
                "provider": provider,
                "status": "healthy",
                "latency_ms": 50,
                "error": None
            })
        else:
            has_key = False
            if provider == "openai":
                has_key = bool(os.environ.get("OPENAI_API_KEY"))
            elif provider == "anthropic":
                has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
            
            results.append({
                "provider": provider,
                "status": "healthy" if has_key else "no_api_key",
                "latency_ms": None,
                "error": None if has_key else "API key not configured"
            })
    
    return {"health_checks": results}


@router.post("/router/test")
async def test_routing(
    model: str,
    current_user: dict = Depends(RequirePermission(Permission.GATEWAY_USE)),
    db: Session = Depends(get_db)
):
    """Test routing to a specific model"""
    import time
    
    try:
        start_time = time.time()
        
        result = await router_service.chat_completion(
            model=model,
            messages=[{"role": "user", "content": "Respond with OK"}],
            max_tokens=10,
            tenant_id=int(current_user["sub"]),
            api_key_id=None,
            user_id=None
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "model": result.get("model", model),
            "provider": result.get("provider", "unknown"),
            "latency_ms": latency_ms,
            "usage": result.get("usage", {})
        }
    except Exception as e:
        return {
            "success": False,
            "model": model,
            "provider": "unknown",
            "error": str(e)
        }


@router.get("/router/stats")
async def get_routing_stats(
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW)),
    db: Session = Depends(get_db)
):
    """Get routing statistics"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    tenant_id = int(current_user["sub"])
    since = datetime.utcnow() - timedelta(days=7)
    
    stats = db.query(
        UsageLog.provider,
        func.count(UsageLog.id).label("requests"),
        func.sum(UsageLog.total_tokens).label("tokens"),
        func.avg(UsageLog.latency_ms).label("avg_latency")
    ).filter(
        UsageLog.tenant_id == tenant_id,
        UsageLog.created_at >= since
    ).group_by(UsageLog.provider).all()
    
    provider_stats = []
    for stat in stats:
        provider_stats.append({
            "provider": stat.provider or "unknown",
            "requests": stat.requests,
            "tokens": int(stat.tokens or 0),
            "avg_latency_ms": round(stat.avg_latency or 0, 2)
        })
    
    return {"stats": provider_stats, "period": "last_7_days"}
