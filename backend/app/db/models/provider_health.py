"""
Provider Health Tracking Models

Stores circuit breaker states, load balancer metrics, and provider health history
for persistence across restarts and historical analysis.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.app.db.session import Base


class ProviderHealthStatus(Base):
    """Current health status and circuit breaker state for each provider."""
    __tablename__ = "provider_health_status"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    
    provider_name = Column(String(100), nullable=False, index=True)
    
    # Circuit Breaker State
    circuit_state = Column(String(20), default="closed")  # closed, open, half_open
    failure_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    consecutive_failures = Column(Integer, default=0)
    consecutive_successes = Column(Integer, default=0)
    
    last_failure_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    circuit_opened_at = Column(DateTime, nullable=True)
    
    # Circuit Breaker Configuration
    failure_threshold = Column(Integer, default=5)
    success_threshold = Column(Integer, default=2)
    timeout_seconds = Column(Integer, default=30)
    window_seconds = Column(Integer, default=60)
    
    # Health Metrics
    is_healthy = Column(Boolean, default=True)
    health_check_failures = Column(Integer, default=0)
    last_health_check_at = Column(DateTime, nullable=True)
    
    # Load Balancer Metrics
    active_requests = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    avg_latency_ms = Column(Float, default=0.0)
    
    # Provider Metadata
    endpoint_url = Column(String(500), nullable=True)
    provider_config_id = Column(Integer, ForeignKey("provider_configs_v2.id"), nullable=True)
    
    metadata_ = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    provider_config = relationship("EnhancedProviderConfig", foreign_keys=[provider_config_id])
    health_history = relationship("ProviderHealthHistory", back_populates="provider_status", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class ProviderHealthHistory(Base):
    """Historical health events for providers (failures, recoveries, state changes)."""
    __tablename__ = "provider_health_history"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_status_id = Column(Integer, ForeignKey("provider_health_status.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    
    provider_name = Column(String(100), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False, index=True)
    # Event types: circuit_opened, circuit_closed, circuit_half_open, 
    #              failure, success, health_check_failed, health_check_passed
    
    event_details = Column(JSON, default=dict)
    
    # Circuit Breaker State at time of event
    circuit_state_before = Column(String(20), nullable=True)
    circuit_state_after = Column(String(20), nullable=True)
    
    # Metrics at time of event
    failure_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    latency_ms = Column(Float, nullable=True)
    
    error_message = Column(Text, nullable=True)
    error_category = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    provider_status = relationship("ProviderHealthStatus", back_populates="health_history")
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class LoadBalancerMetrics(Base):
    """Aggregated load balancer metrics per provider group."""
    __tablename__ = "load_balancer_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    
    group_name = Column(String(100), nullable=False, index=True)
    provider_name = Column(String(100), nullable=False, index=True)
    
    # Strategy used
    strategy = Column(String(50), default="weighted_round_robin")
    weight = Column(Integer, default=1)
    
    # Request Metrics (aggregated per hour/day)
    time_bucket = Column(DateTime, nullable=False, index=True)  # Hourly bucket
    bucket_type = Column(String(20), default="hourly")  # hourly, daily
    
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    
    total_latency_ms = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    min_latency_ms = Column(Float, nullable=True)
    max_latency_ms = Column(Float, nullable=True)
    
    # Load Distribution
    requests_percentage = Column(Float, default=0.0)  # % of total group requests
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class CircuitBreakerEvent(Base):
    """Real-time circuit breaker state changes for alerting and monitoring."""
    __tablename__ = "circuit_breaker_events"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    
    provider_name = Column(String(100), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False)
    # opened, closed, half_open, forced_open, forced_close, reset
    
    state_before = Column(String(20), nullable=False)
    state_after = Column(String(20), nullable=False)
    
    failure_count = Column(Integer, default=0)
    consecutive_failures = Column(Integer, default=0)
    
    trigger_reason = Column(String(255), nullable=True)
    # "failure_threshold_exceeded", "success_threshold_reached", "manual_override", etc.
    
    triggered_by = Column(String(100), nullable=True)  # user_id or "system"
    
    duration_in_state_seconds = Column(Integer, nullable=True)
    
    metadata_ = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
