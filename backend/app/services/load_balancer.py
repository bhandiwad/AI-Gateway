"""
Load Balancer Service for AI Gateway

Distributes requests across multiple providers based on different strategies:
- Weighted Round Robin: Distribute based on assigned weights
- Round Robin: Equal distribution
- Least Connections: Route to provider with fewest active requests
- Random: Random provider selection
"""

import random
import threading
import time
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(str, Enum):
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    LEAST_LATENCY = "least_latency"


@dataclass
class ProviderEndpoint:
    """Represents a provider endpoint with load balancing metadata"""
    name: str
    weight: int = 1
    is_healthy: bool = True
    active_requests: int = 0
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    last_used_at: float = 0.0
    

class LoadBalancer:
    """
    Load balancer for distributing requests across multiple provider endpoints.
    Thread-safe implementation with real-time metrics tracking.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        # provider_group -> List[ProviderEndpoint]
        self._provider_pools: Dict[str, List[ProviderEndpoint]] = defaultdict(list)
        # Round-robin counters per group
        self._rr_counters: Dict[str, int] = defaultdict(int)
        # Strategy per group (default: weighted_round_robin)
        self._strategies: Dict[str, LoadBalancingStrategy] = {}
        
    def register_provider_pool(
        self,
        group_name: str,
        providers: List[Dict],
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN
    ):
        """
        Register a pool of providers for a group (e.g., "gpt-4" or "claude")
        
        Args:
            group_name: Identifier for the provider group
            providers: List of provider configs with 'name' and optional 'weight'
            strategy: Load balancing strategy to use
        """
        with self._lock:
            self._provider_pools[group_name] = [
                ProviderEndpoint(
                    name=p.get("name"),
                    weight=p.get("weight", 1),
                    is_healthy=p.get("is_healthy", True)
                )
                for p in providers
            ]
            self._strategies[group_name] = strategy
            logger.info(
                f"Registered provider pool '{group_name}' with {len(providers)} "
                f"providers using {strategy.value} strategy"
            )
    
    def select_provider(
        self,
        group_name: str,
        exclude_providers: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Select the best provider from a group based on the configured strategy.
        
        Args:
            group_name: The provider group to select from
            exclude_providers: List of provider names to exclude (e.g., already failed)
            
        Returns:
            Selected provider name or None if no healthy providers available
        """
        with self._lock:
            providers = self._provider_pools.get(group_name, [])
            if not providers:
                logger.warning(f"No providers registered for group '{group_name}'")
                return None
            
            # Filter out unhealthy and excluded providers
            exclude_set = set(exclude_providers or [])
            healthy_providers = [
                p for p in providers
                if p.is_healthy and p.name not in exclude_set
            ]
            
            if not healthy_providers:
                logger.warning(
                    f"No healthy providers available for group '{group_name}'. "
                    f"Total: {len(providers)}, Excluded: {len(exclude_set)}"
                )
                return None
            
            strategy = self._strategies.get(group_name, LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN)
            
            if strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                selected = self._weighted_round_robin(group_name, healthy_providers)
            elif strategy == LoadBalancingStrategy.ROUND_ROBIN:
                selected = self._round_robin(group_name, healthy_providers)
            elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                selected = self._least_connections(healthy_providers)
            elif strategy == LoadBalancingStrategy.LEAST_LATENCY:
                selected = self._least_latency(healthy_providers)
            elif strategy == LoadBalancingStrategy.RANDOM:
                selected = self._random_selection(healthy_providers)
            else:
                selected = healthy_providers[0]
            
            # Update usage tracking
            if selected:
                selected.last_used_at = time.time()
                logger.debug(f"Selected provider '{selected.name}' from group '{group_name}'")
            
            return selected.name if selected else None
    
    def _weighted_round_robin(
        self,
        group_name: str,
        providers: List[ProviderEndpoint]
    ) -> Optional[ProviderEndpoint]:
        """Weighted round-robin: Select based on provider weights"""
        if not providers:
            return None
        
        # Calculate total weight
        total_weight = sum(p.weight for p in providers)
        if total_weight == 0:
            # Fallback to equal weights
            return self._round_robin(group_name, providers)
        
        # Increment counter
        counter = self._rr_counters[group_name]
        self._rr_counters[group_name] = (counter + 1) % total_weight
        
        # Select provider based on weighted position
        cumulative_weight = 0
        target_position = counter % total_weight
        
        for provider in providers:
            cumulative_weight += provider.weight
            if target_position < cumulative_weight:
                return provider
        
        # Fallback
        return providers[0]
    
    def _round_robin(
        self,
        group_name: str,
        providers: List[ProviderEndpoint]
    ) -> Optional[ProviderEndpoint]:
        """Simple round-robin: Equal distribution"""
        if not providers:
            return None
        
        counter = self._rr_counters[group_name]
        self._rr_counters[group_name] = (counter + 1) % len(providers)
        
        return providers[counter % len(providers)]
    
    def _least_connections(
        self,
        providers: List[ProviderEndpoint]
    ) -> Optional[ProviderEndpoint]:
        """Select provider with fewest active connections"""
        if not providers:
            return None
        
        return min(providers, key=lambda p: p.active_requests)
    
    def _least_latency(
        self,
        providers: List[ProviderEndpoint]
    ) -> Optional[ProviderEndpoint]:
        """Select provider with lowest average latency"""
        if not providers:
            return None
        
        # Filter providers with tracked latency
        providers_with_latency = [p for p in providers if p.total_requests > 0]
        
        if not providers_with_latency:
            # Fallback to round-robin if no latency data
            return providers[0]
        
        return min(providers_with_latency, key=lambda p: p.avg_latency_ms)
    
    def _random_selection(
        self,
        providers: List[ProviderEndpoint]
    ) -> Optional[ProviderEndpoint]:
        """Random provider selection"""
        if not providers:
            return None
        
        # Weighted random based on weights
        weights = [p.weight for p in providers]
        return random.choices(providers, weights=weights, k=1)[0]
    
    def mark_request_start(self, group_name: str, provider_name: str):
        """Mark that a request has started to a provider"""
        with self._lock:
            providers = self._provider_pools.get(group_name, [])
            for provider in providers:
                if provider.name == provider_name:
                    provider.active_requests += 1
                    provider.total_requests += 1
                    break
    
    def mark_request_end(
        self,
        group_name: str,
        provider_name: str,
        latency_ms: float,
        success: bool = True
    ):
        """
        Mark that a request has completed.
        Updates active connection count and moving average latency.
        """
        with self._lock:
            providers = self._provider_pools.get(group_name, [])
            for provider in providers:
                if provider.name == provider_name:
                    provider.active_requests = max(0, provider.active_requests - 1)
                    
                    # Update moving average latency (exponential moving average)
                    alpha = 0.3  # Smoothing factor
                    if provider.avg_latency_ms == 0:
                        provider.avg_latency_ms = latency_ms
                    else:
                        provider.avg_latency_ms = (
                            alpha * latency_ms + 
                            (1 - alpha) * provider.avg_latency_ms
                        )
                    
                    logger.debug(
                        f"Provider '{provider_name}': active={provider.active_requests}, "
                        f"avg_latency={provider.avg_latency_ms:.2f}ms"
                    )
                    break
    
    def update_provider_health(
        self,
        group_name: str,
        provider_name: str,
        is_healthy: bool
    ):
        """Update health status of a provider"""
        with self._lock:
            providers = self._provider_pools.get(group_name, [])
            for provider in providers:
                if provider.name == provider_name:
                    old_status = provider.is_healthy
                    provider.is_healthy = is_healthy
                    if old_status != is_healthy:
                        status_str = "healthy" if is_healthy else "unhealthy"
                        logger.info(
                            f"Provider '{provider_name}' in group '{group_name}' "
                            f"marked as {status_str}"
                        )
                    break
    
    def get_provider_stats(self, group_name: str) -> List[Dict]:
        """Get statistics for all providers in a group"""
        with self._lock:
            providers = self._provider_pools.get(group_name, [])
            return [
                {
                    "name": p.name,
                    "weight": p.weight,
                    "is_healthy": p.is_healthy,
                    "active_requests": p.active_requests,
                    "total_requests": p.total_requests,
                    "avg_latency_ms": round(p.avg_latency_ms, 2),
                    "last_used_at": p.last_used_at
                }
                for p in providers
            ]
    
    def get_all_stats(self) -> Dict[str, List[Dict]]:
        """Get statistics for all provider groups"""
        with self._lock:
            return {
                group: self.get_provider_stats(group)
                for group in self._provider_pools.keys()
            }
    
    def reset_stats(self, group_name: Optional[str] = None):
        """Reset statistics for a group or all groups"""
        with self._lock:
            groups = [group_name] if group_name else list(self._provider_pools.keys())
            
            for group in groups:
                providers = self._provider_pools.get(group, [])
                for provider in providers:
                    provider.active_requests = 0
                    provider.total_requests = 0
                    provider.avg_latency_ms = 0.0
                    provider.last_used_at = 0.0
            
            logger.info(f"Reset statistics for groups: {groups}")


# Global load balancer instance
load_balancer = LoadBalancer()
