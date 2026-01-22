"""
Performance Monitoring Middleware
Tracks request latency and identifies bottlenecks
"""
import time
import random
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog

logger = structlog.get_logger()


class PerformanceMonitorMiddleware(BaseHTTPMiddleware):
    """
    Monitors request performance and logs slow requests.
    Adds X-Response-Time header to all responses.
    """
    
    def __init__(self, app, slow_request_threshold_ms: int = 100, sample_rate: float = 0.1):
        super().__init__(app)
        self.slow_threshold = slow_request_threshold_ms / 1000.0
        self.sample_rate = sample_rate
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate latency
        latency_seconds = time.time() - start_time
        latency_ms = latency_seconds * 1000
        
        # Add header
        response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
        
        # Log slow requests or sample normal requests
        if latency_seconds > self.slow_threshold:
            logger.warning(
                "slow_request",
                path=request.url.path,
                method=request.method,
                latency_ms=round(latency_ms, 2),
                status_code=response.status_code
            )
        elif random.random() < self.sample_rate:
            # Sample 10% of normal requests for performance tracking
            logger.info(
                "request_sample",
                path=request.url.path,
                method=request.method,
                latency_ms=round(latency_ms, 2),
                status_code=response.status_code
            )
        
        return response
