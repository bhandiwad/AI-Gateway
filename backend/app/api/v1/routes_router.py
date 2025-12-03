from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import yaml
import os

from backend.app.db.session import get_db
from backend.app.core.security import get_current_user
from backend.app.core.permissions import Permission, RequirePermission
from backend.app.services.router_service import router_service
from backend.app.services.model_settings_service import model_settings_service
from backend.app.db.models.usage_log import UsageLog

router = APIRouter()


class ModelSettingsUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    display_order: Optional[int] = None


class ModelReorderRequest(BaseModel):
    model_order: List[str]


class CustomModelCreate(BaseModel):
    model_id: str
    name: str
    provider: str = "custom"
    context_length: int = 128000
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    supports_streaming: bool = True
    supports_functions: bool = False
    supports_vision: bool = False
    api_base_url: Optional[str] = None
    api_key_name: Optional[str] = None
    is_enabled: bool = True


class RateLimitTierUpdate(BaseModel):
    name: str
    requests_per_minute: int
    tokens_per_minute: int


class RoutingConfigUpdate(BaseModel):
    default_provider: Optional[str] = None
    default_model: Optional[str] = None
    fallback_enabled: Optional[bool] = None
    max_retries: Optional[int] = None
    fallback_order: Optional[List[str]] = None
    rate_limit_tiers: Optional[List[RateLimitTierUpdate]] = None
    default_rate_limit_requests: Optional[int] = None
    default_rate_limit_tokens: Optional[int] = None


class CustomModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    context_length: Optional[int] = None
    input_cost_per_1k: Optional[float] = None
    output_cost_per_1k: Optional[float] = None
    supports_streaming: Optional[bool] = None
    supports_functions: Optional[bool] = None
    supports_vision: Optional[bool] = None
    api_base_url: Optional[str] = None
    api_key_name: Optional[str] = None
    is_enabled: Optional[bool] = None

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


def save_routing_config(config: dict):
    """Save routing configuration to YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), '../../..', 'configs', 'routing_rules.yaml')
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


@router.put("/router/config")
async def update_router_config(
    update_data: RoutingConfigUpdate,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT)),
    db: Session = Depends(get_db)
):
    """Update routing configuration"""
    config = load_routing_config()
    routing = config.get("routing", {})
    
    if update_data.default_provider is not None:
        routing["default_provider"] = update_data.default_provider
    
    if update_data.default_model is not None:
        routing["default_model"] = update_data.default_model
    
    if "fallback" not in routing:
        routing["fallback"] = {}
    
    if update_data.fallback_enabled is not None:
        routing["fallback"]["enabled"] = update_data.fallback_enabled
    
    if update_data.max_retries is not None:
        routing["fallback"]["max_retries"] = update_data.max_retries
    
    if update_data.fallback_order is not None:
        routing["fallback"]["fallback_order"] = update_data.fallback_order
    
    if "rate_limits" not in routing:
        routing["rate_limits"] = {"default": {}, "tiers": {}}
    
    if update_data.default_rate_limit_requests is not None:
        routing["rate_limits"]["default"]["requests_per_minute"] = update_data.default_rate_limit_requests
    
    if update_data.default_rate_limit_tokens is not None:
        routing["rate_limits"]["default"]["tokens_per_minute"] = update_data.default_rate_limit_tokens
    
    if update_data.rate_limit_tiers is not None:
        routing["rate_limits"]["tiers"] = {}
        for tier in update_data.rate_limit_tiers:
            routing["rate_limits"]["tiers"][tier.name] = {
                "requests_per_minute": tier.requests_per_minute,
                "tokens_per_minute": tier.tokens_per_minute
            }
    
    config["routing"] = routing
    save_routing_config(config)
    
    return {"message": "Configuration updated successfully", "config": routing}


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


@router.get("/models/settings")
async def get_model_settings(
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW)),
    db: Session = Depends(get_db)
):
    """Get all models with tenant-specific settings (enabled/disabled, order)"""
    tenant_id = int(current_user["sub"])
    models = model_settings_service.get_models_for_tenant(db, tenant_id)
    return {"models": models}


@router.put("/models/{model_id}/settings")
async def update_model_settings(
    model_id: str,
    settings: ModelSettingsUpdate,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT)),
    db: Session = Depends(get_db)
):
    """Update settings for a specific model"""
    tenant_id = int(current_user["sub"])
    result = model_settings_service.update_model_settings(
        db=db,
        tenant_id=tenant_id,
        model_id=model_id,
        is_enabled=settings.is_enabled,
        display_order=settings.display_order
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found"
        )
    
    return result


@router.put("/models/{model_id}/toggle")
async def toggle_model(
    model_id: str,
    enabled: bool = Query(...),
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT)),
    db: Session = Depends(get_db)
):
    """Enable or disable a model for this tenant"""
    tenant_id = int(current_user["sub"])
    result = model_settings_service.toggle_model(
        db=db,
        tenant_id=tenant_id,
        model_id=model_id,
        is_enabled=enabled
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_id}' not found"
        )
    
    return result


@router.post("/models/reorder")
async def reorder_models(
    request: ModelReorderRequest,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT)),
    db: Session = Depends(get_db)
):
    """Reorder models for this tenant"""
    tenant_id = int(current_user["sub"])
    models = model_settings_service.reorder_models(
        db=db,
        tenant_id=tenant_id,
        model_order=request.model_order
    )
    
    return {"models": models, "message": "Models reordered successfully"}


@router.post("/models/custom")
async def create_custom_model(
    model_data: CustomModelCreate,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT)),
    db: Session = Depends(get_db)
):
    """Create a custom model for this tenant"""
    tenant_id = int(current_user["sub"])
    try:
        model = model_settings_service.create_custom_model(
            db=db,
            tenant_id=tenant_id,
            model_data=model_data.model_dump()
        )
        return model
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/models/custom/{model_id}")
async def update_custom_model(
    model_id: str,
    model_data: CustomModelUpdate,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT)),
    db: Session = Depends(get_db)
):
    """Update a custom model for this tenant"""
    tenant_id = int(current_user["sub"])
    result = model_settings_service.update_custom_model(
        db=db,
        tenant_id=tenant_id,
        model_id=model_id,
        model_data=model_data.model_dump(exclude_unset=True)
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Custom model '{model_id}' not found"
        )
    
    return result


@router.delete("/models/custom/{model_id}")
async def delete_custom_model(
    model_id: str,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT)),
    db: Session = Depends(get_db)
):
    """Delete a custom model for this tenant"""
    tenant_id = int(current_user["sub"])
    success = model_settings_service.delete_custom_model(
        db=db,
        tenant_id=tenant_id,
        model_id=model_id
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Custom model '{model_id}' not found"
        )
    
    return {"message": f"Model '{model_id}' deleted successfully"}
