"""
Load Balancer and Circuit Breaker Management API

Provides endpoints to:
- Configure load balancing strategies
- Monitor provider health via circuit breakers
- View real-time metrics and statistics
- Manage circuit breaker states
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel

from backend.app.db.session import get_db
from backend.app.core.permissions import Permission, RequirePermission
from backend.app.services.load_balancer import (
    load_balancer,
    LoadBalancingStrategy
)
from backend.app.services.circuit_breaker import (
    circuit_breaker_manager,
    CircuitBreakerConfig
)

router = APIRouter()


# Pydantic Models
class ProviderEndpointConfig(BaseModel):
    name: str
    weight: int = 1
    is_healthy: bool = True


class LoadBalancerPoolConfig(BaseModel):
    group_name: str
    providers: List[ProviderEndpointConfig]
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN


class CircuitBreakerConfigUpdate(BaseModel):
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 30
    window_seconds: int = 60
    half_open_max_requests: int = 3


class ProviderHealthUpdate(BaseModel):
    is_healthy: bool


# Load Balancer Endpoints

@router.get("/load-balancer/stats")
async def get_load_balancer_stats(
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW))
):
    """Get load balancer statistics for all provider groups"""
    stats = load_balancer.get_all_stats()
    return {
        "stats": stats,
        "total_groups": len(stats)
    }


@router.get("/load-balancer/stats/{group_name}")
async def get_group_stats(
    group_name: str,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW))
):
    """Get load balancer statistics for a specific provider group"""
    stats = load_balancer.get_provider_stats(group_name)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Provider group '{group_name}' not found")
    
    return {
        "group_name": group_name,
        "providers": stats
    }


@router.post("/load-balancer/pools")
async def register_provider_pool(
    config: LoadBalancerPoolConfig,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT))
):
    """Register or update a provider pool for load balancing"""
    try:
        providers = [p.model_dump() for p in config.providers]
        load_balancer.register_provider_pool(
            config.group_name,
            providers,
            config.strategy
        )
        return {
            "message": f"Provider pool '{config.group_name}' registered successfully",
            "group_name": config.group_name,
            "provider_count": len(providers),
            "strategy": config.strategy.value
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/load-balancer/pools/{group_name}/health/{provider_name}")
async def update_provider_health(
    group_name: str,
    provider_name: str,
    health_update: ProviderHealthUpdate,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT))
):
    """Update health status of a provider in a load balancing group"""
    load_balancer.update_provider_health(
        group_name,
        provider_name,
        health_update.is_healthy
    )
    return {
        "message": f"Provider '{provider_name}' health updated",
        "group_name": group_name,
        "provider_name": provider_name,
        "is_healthy": health_update.is_healthy
    }


@router.post("/load-balancer/pools/{group_name}/reset")
async def reset_pool_stats(
    group_name: str,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT))
):
    """Reset statistics for a load balancing pool"""
    load_balancer.reset_stats(group_name)
    return {
        "message": f"Statistics reset for group '{group_name}'"
    }


# Circuit Breaker Endpoints

@router.get("/circuit-breakers")
async def get_all_circuit_breakers(
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW))
):
    """Get status and metrics for all circuit breakers"""
    metrics = circuit_breaker_manager.get_all_metrics()
    
    # Categorize by state
    closed = [m for m in metrics.values() if m["state"] == "closed"]
    open_breakers = [m for m in metrics.values() if m["state"] == "open"]
    half_open = [m for m in metrics.values() if m["state"] == "half_open"]
    
    return {
        "circuit_breakers": metrics,
        "summary": {
            "total": len(metrics),
            "closed": len(closed),
            "open": len(open_breakers),
            "half_open": len(half_open)
        },
        "unhealthy_providers": circuit_breaker_manager.get_unhealthy_providers()
    }


@router.get("/circuit-breakers/{provider_name}")
async def get_circuit_breaker(
    provider_name: str,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW))
):
    """Get detailed metrics for a specific circuit breaker"""
    breaker = circuit_breaker_manager.get_breaker(provider_name)
    return breaker.get_metrics()


@router.post("/circuit-breakers/{provider_name}/force-open")
async def force_circuit_open(
    provider_name: str,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT))
):
    """Manually force a circuit breaker to OPEN state"""
    breaker = circuit_breaker_manager.get_breaker(provider_name)
    breaker.force_open()
    return {
        "message": f"Circuit breaker for '{provider_name}' forced to OPEN",
        "state": breaker.state.value
    }


@router.post("/circuit-breakers/{provider_name}/force-close")
async def force_circuit_close(
    provider_name: str,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT))
):
    """Manually force a circuit breaker to CLOSED state"""
    breaker = circuit_breaker_manager.get_breaker(provider_name)
    breaker.force_close()
    return {
        "message": f"Circuit breaker for '{provider_name}' forced to CLOSED",
        "state": breaker.state.value
    }


@router.post("/circuit-breakers/{provider_name}/reset")
async def reset_circuit_breaker(
    provider_name: str,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT))
):
    """Reset a circuit breaker to initial state"""
    circuit_breaker_manager.reset_breaker(provider_name)
    return {
        "message": f"Circuit breaker for '{provider_name}' reset"
    }


@router.post("/circuit-breakers/reset-all")
async def reset_all_circuit_breakers(
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT))
):
    """Reset all circuit breakers"""
    circuit_breaker_manager.reset_all()
    return {
        "message": "All circuit breakers reset"
    }


@router.put("/circuit-breakers/config")
async def update_circuit_breaker_config(
    config: CircuitBreakerConfigUpdate,
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_EDIT))
):
    """Update default circuit breaker configuration"""
    cb_config = CircuitBreakerConfig(
        failure_threshold=config.failure_threshold,
        success_threshold=config.success_threshold,
        timeout_seconds=config.timeout_seconds,
        window_seconds=config.window_seconds,
        half_open_max_requests=config.half_open_max_requests
    )
    circuit_breaker_manager.set_default_config(cb_config)
    return {
        "message": "Default circuit breaker configuration updated",
        "config": config.model_dump()
    }


# Combined Health Dashboard

@router.get("/health-dashboard")
async def get_health_dashboard(
    current_user: dict = Depends(RequirePermission(Permission.ROUTER_VIEW))
):
    """Get combined health dashboard with load balancer and circuit breaker data"""
    lb_stats = load_balancer.get_all_stats()
    cb_metrics = circuit_breaker_manager.get_all_metrics()
    
    # Combine data by provider
    providers_health = {}
    
    # Add load balancer data
    for group, providers in lb_stats.items():
        for provider in providers:
            provider_name = provider["name"]
            if provider_name not in providers_health:
                providers_health[provider_name] = {
                    "name": provider_name,
                    "groups": []
                }
            providers_health[provider_name]["groups"].append({
                "group": group,
                "weight": provider["weight"],
                "is_healthy": provider["is_healthy"],
                "active_requests": provider["active_requests"],
                "total_requests": provider["total_requests"],
                "avg_latency_ms": provider["avg_latency_ms"]
            })
    
    # Add circuit breaker data
    for provider_name, cb_data in cb_metrics.items():
        if provider_name not in providers_health:
            providers_health[provider_name] = {
                "name": provider_name,
                "groups": []
            }
        providers_health[provider_name]["circuit_breaker"] = {
            "state": cb_data["state"],
            "failure_count": cb_data["failure_count"],
            "success_count": cb_data["success_count"],
            "consecutive_failures": cb_data["consecutive_failures"],
            "rejected_requests": cb_data["rejected_requests"],
            "failures_in_window": cb_data["failures_in_window"]
        }
    
    return {
        "providers": list(providers_health.values()),
        "summary": {
            "total_providers": len(providers_health),
            "circuit_breakers_open": len([
                p for p in providers_health.values()
                if p.get("circuit_breaker", {}).get("state") == "open"
            ]),
            "load_balancer_groups": len(lb_stats)
        }
    }
