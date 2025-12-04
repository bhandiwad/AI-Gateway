"""
Circuit Breaker Service for AI Gateway

Implements circuit breaker pattern to prevent cascading failures:
- CLOSED: Normal operation, requests pass through
- OPEN: Provider failing, reject requests immediately for cooldown period
- HALF_OPEN: Testing if provider recovered, allow limited requests

Features:
- Per-provider state management
- Configurable failure thresholds and timeouts
- Automatic state transitions
- Health recovery detection
"""

import time
import threading
from typing import Dict, Callable, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import structlog
import asyncio
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker"""
    failure_threshold: int = 5          # Failures before opening circuit
    success_threshold: int = 2          # Successes in HALF_OPEN to close
    timeout_seconds: int = 30           # Time to wait before HALF_OPEN
    window_seconds: int = 60            # Time window for counting failures
    half_open_max_requests: int = 3     # Max concurrent requests in HALF_OPEN


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring"""
    failure_count: int = 0
    success_count: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    total_requests: int = 0
    rejected_requests: int = 0
    state_changed_at: float = field(default_factory=time.time)
    
    # Sliding window for failures
    failure_timestamps: list = field(default_factory=list)


class CircuitBreaker:
    """
    Circuit breaker for a single provider.
    Thread-safe implementation with automatic state management.
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._lock = threading.RLock()
        self._half_open_requests = 0
        
        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"failure_threshold={self.config.failure_threshold}, "
            f"timeout={self.config.timeout_seconds}s"
        )
    
    def can_execute(self) -> bool:
        """
        Check if request can be executed.
        
        Returns:
            True if request should be allowed, False if circuit is open
        """
        with self._lock:
            self.metrics.total_requests += 1
            
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                # Check if timeout has passed
                time_since_open = time.time() - self.metrics.state_changed_at
                if time_since_open >= self.config.timeout_seconds:
                    logger.info(f"Circuit '{self.name}': OPEN → HALF_OPEN (timeout elapsed)")
                    self._transition_to_half_open()
                    return True
                else:
                    self.metrics.rejected_requests += 1
                    logger.debug(
                        f"Circuit '{self.name}': Request rejected (OPEN state), "
                        f"retry in {self.config.timeout_seconds - time_since_open:.1f}s"
                    )
                    return False
            
            elif self.state == CircuitState.HALF_OPEN:
                # Allow limited concurrent requests in HALF_OPEN
                if self._half_open_requests < self.config.half_open_max_requests:
                    self._half_open_requests += 1
                    return True
                else:
                    self.metrics.rejected_requests += 1
                    logger.debug(
                        f"Circuit '{self.name}': Request rejected "
                        f"(HALF_OPEN max concurrent reached)"
                    )
                    return False
            
            return False
    
    def record_success(self, latency_ms: Optional[float] = None):
        """Record a successful request"""
        with self._lock:
            self.metrics.success_count += 1
            self.metrics.consecutive_successes += 1
            self.metrics.consecutive_failures = 0
            self.metrics.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self._half_open_requests = max(0, self._half_open_requests - 1)
                
                if self.metrics.consecutive_successes >= self.config.success_threshold:
                    logger.info(
                        f"Circuit '{self.name}': HALF_OPEN → CLOSED "
                        f"({self.metrics.consecutive_successes} consecutive successes)"
                    )
                    self._transition_to_closed()
            
            logger.debug(
                f"Circuit '{self.name}': Success recorded "
                f"(consecutive: {self.metrics.consecutive_successes})"
            )
    
    def record_failure(self, error: Optional[Exception] = None, db: Optional[Session] = None):
        """Record a failed request"""
        logger.warning(
            "circuit_breaker_opened",
            provider=self.name,
            failure_count=self.metrics.failure_count,
            consecutive_failures=self.metrics.consecutive_failures
        )
        
        # Trigger alert
        if db:
            try:
                from backend.app.services.alert_service import alert_service
                from backend.app.db.models.alerts import AlertType, AlertSeverity
                asyncio.create_task(
                    alert_service.trigger_alert(
                        db=db,
                        tenant_id=0,  # System-level alert
                        alert_type=AlertType.CIRCUIT_BREAKER_OPENED,
                        title=f"Circuit Breaker Opened: {self.name}",
                        message=f"Provider {self.name} circuit breaker has opened due to {self.metrics.consecutive_failures} consecutive failures.",
                        context={
                            "provider_name": self.name,
                            "failure_count": self.metrics.failure_count,
                            "consecutive_failures": self.metrics.consecutive_failures,
                            "circuit_state": "open"
                        },
                        severity=AlertSeverity.ERROR
                    )
                )
            except Exception as e:
                logger.error(f"Failed to trigger circuit breaker alert: {e}")
        
        with self._lock:
            current_time = time.time()
            self.metrics.failure_count += 1
            self.metrics.consecutive_failures += 1
            self.metrics.consecutive_successes = 0
            self.metrics.last_failure_time = current_time
            
            # Add to sliding window
            self.metrics.failure_timestamps.append(current_time)
            
            # Clean old failures outside window
            window_start = current_time - self.config.window_seconds
            self.metrics.failure_timestamps = [
                ts for ts in self.metrics.failure_timestamps
                if ts >= window_start
            ]
            
            if self.state == CircuitState.HALF_OPEN:
                self._half_open_requests = max(0, self._half_open_requests - 1)
                logger.warning(
                    f"Circuit '{self.name}': Failure in HALF_OPEN state, "
                    f"transitioning to OPEN"
                )
                self._transition_to_open()
            
            elif self.state == CircuitState.CLOSED:
                failures_in_window = len(self.metrics.failure_timestamps)
                
                if failures_in_window >= self.config.failure_threshold:
                    logger.warning(
                        f"Circuit '{self.name}': Failure threshold reached "
                        f"({failures_in_window}/{self.config.failure_threshold}), "
                        f"transitioning to OPEN"
                    )
                    self._transition_to_open()
                else:
                    logger.debug(
                        f"Circuit '{self.name}': Failure recorded "
                        f"({failures_in_window}/{self.config.failure_threshold} in window)"
                    )
    
    def _transition_to_open(self, db: Optional[Session] = None):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.metrics.state_changed_at = time.time()
        self.metrics.consecutive_successes = 0
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.metrics.state_changed_at = time.time()
        self.metrics.consecutive_successes = 0
        self.metrics.consecutive_failures = 0
        self._half_open_requests = 0
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.metrics.state_changed_at = time.time()
        self.metrics.consecutive_failures = 0
        self.metrics.failure_timestamps.clear()
    
    def force_open(self):
        """Manually force circuit to OPEN state"""
        with self._lock:
            logger.warning(f"Circuit '{self.name}': Manually forced to OPEN")
            self._transition_to_open()
    
    def force_close(self):
        """Manually force circuit to CLOSED state"""
        with self._lock:
            logger.info(f"Circuit '{self.name}': Manually forced to CLOSED")
            self._transition_to_closed()
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        with self._lock:
            logger.info(f"Circuit '{self.name}': Reset to initial state")
            self.state = CircuitState.CLOSED
            self.metrics = CircuitBreakerMetrics()
            self._half_open_requests = 0
    
    def get_metrics(self) -> Dict:
        """Get current metrics and state"""
        with self._lock:
            time_in_state = time.time() - self.metrics.state_changed_at
            failures_in_window = len(self.metrics.failure_timestamps)
            
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.metrics.failure_count,
                "success_count": self.metrics.success_count,
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "total_requests": self.metrics.total_requests,
                "rejected_requests": self.metrics.rejected_requests,
                "failures_in_window": failures_in_window,
                "time_in_current_state_seconds": round(time_in_state, 2),
                "last_failure_time": self.metrics.last_failure_time,
                "last_success_time": self.metrics.last_success_time,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "success_threshold": self.config.success_threshold,
                    "timeout_seconds": self.config.timeout_seconds,
                    "window_seconds": self.config.window_seconds
                }
            }


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different providers.
    Singleton pattern for global access.
    """
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
        self._default_config = CircuitBreakerConfig()
    
    def get_breaker(
        self,
        provider_name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a provider.
        
        Args:
            provider_name: Unique identifier for the provider
            config: Optional custom configuration
            
        Returns:
            CircuitBreaker instance
        """
        with self._lock:
            if provider_name not in self._breakers:
                breaker_config = config or self._default_config
                self._breakers[provider_name] = CircuitBreaker(
                    name=provider_name,
                    config=breaker_config
                )
            return self._breakers[provider_name]
    
    def execute_with_breaker(
        self,
        provider_name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            provider_name: Provider identifier
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Result from function execution
            
        Raises:
            Exception: If circuit is open or function fails
        """
        breaker = self.get_breaker(provider_name)
        
        if not breaker.can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker for '{provider_name}' is OPEN. "
                f"Service temporarily unavailable."
            )
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            breaker.record_success(latency_ms)
            return result
        except Exception as e:
            breaker.record_failure(e)
            raise
    
    async def execute_with_breaker_async(
        self,
        provider_name: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Async version of execute_with_breaker"""
        breaker = self.get_breaker(provider_name)
        
        if not breaker.can_execute():
            raise CircuitBreakerOpenError(
                f"Circuit breaker for '{provider_name}' is OPEN. "
                f"Service temporarily unavailable."
            )
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            breaker.record_success(latency_ms)
            return result
        except Exception as e:
            breaker.record_failure(e)
            raise
    
    def set_default_config(self, config: CircuitBreakerConfig):
        """Set default configuration for new circuit breakers"""
        with self._lock:
            self._default_config = config
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all circuit breakers"""
        with self._lock:
            return {
                name: breaker.get_metrics()
                for name, breaker in self._breakers.items()
            }
    
    def reset_breaker(self, provider_name: str):
        """Reset a specific circuit breaker"""
        with self._lock:
            if provider_name in self._breakers:
                self._breakers[provider_name].reset()
    
    def reset_all(self):
        """Reset all circuit breakers"""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
            logger.info("All circuit breakers reset")
    
    def get_unhealthy_providers(self) -> list[str]:
        """Get list of providers with OPEN circuits"""
        with self._lock:
            return [
                name for name, breaker in self._breakers.items()
                if breaker.state == CircuitState.OPEN
            ]


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()
