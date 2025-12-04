"""
Alert Configuration and Notification Models

Supports multiple alert types and delivery channels:
- Circuit breaker events
- Cost limit warnings
- Provider health issues
- Rate limit warnings
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum

from backend.app.db.session import Base


class AlertType(str, Enum):
    """Types of alerts that can be configured."""
    CIRCUIT_BREAKER_OPENED = "circuit_breaker_opened"
    CIRCUIT_BREAKER_CLOSED = "circuit_breaker_closed"
    PROVIDER_UNHEALTHY = "provider_unhealthy"
    PROVIDER_RECOVERED = "provider_recovered"
    COST_LIMIT_WARNING = "cost_limit_warning"
    COST_LIMIT_EXCEEDED = "cost_limit_exceeded"
    RATE_LIMIT_WARNING = "rate_limit_warning"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_LATENCY = "high_latency"
    QUOTA_EXHAUSTED = "quota_exhausted"


class AlertChannel(str, Enum):
    """Delivery channels for alerts."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    IN_APP = "in_app"
    SMS = "sms"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertConfig(Base):
    """Alert configuration - what to alert on and how."""
    __tablename__ = "alert_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    # What to alert on
    alert_type = Column(SQLEnum(AlertType), nullable=False, index=True)
    
    # Conditions
    conditions = Column(JSON, default=dict)
    # Example conditions:
    # {
    #   "threshold": 0.9,  # For cost warnings (90% of budget)
    #   "provider_names": ["openai", "anthropic"],  # Specific providers
    #   "min_consecutive_failures": 5,  # For circuit breaker
    #   "latency_ms": 5000  # For high latency alerts
    # }
    
    # How to deliver
    channels = Column(JSON, default=list)
    # Example: ["email", "slack", "in_app"]
    
    # Channel-specific configuration
    channel_config = Column(JSON, default=dict)
    # Example:
    # {
    #   "email": {"recipients": ["admin@company.com"]},
    #   "slack": {"webhook_url": "https://...", "channel": "#alerts"},
    #   "webhook": {"url": "https://...", "headers": {...}}
    # }
    
    # Alert frequency control
    cooldown_minutes = Column(Integer, default=15)  # Min time between same alerts
    max_alerts_per_hour = Column(Integer, default=10)
    
    # Severity
    severity = Column(SQLEnum(AlertSeverity), default=AlertSeverity.WARNING)
    
    # Grouping
    group_similar = Column(Boolean, default=True)  # Group similar alerts
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    creator = relationship("User", foreign_keys=[created_by])
    notifications = relationship("AlertNotification", back_populates="alert_config", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class AlertNotification(Base):
    """Individual alert notifications sent."""
    __tablename__ = "alert_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_config_id = Column(Integer, ForeignKey("alert_configs.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Alert details
    alert_type = Column(SQLEnum(AlertType), nullable=False, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    
    # Context
    context = Column(JSON, default=dict)
    # Example:
    # {
    #   "provider_name": "openai",
    #   "circuit_state": "open",
    #   "failure_count": 5,
    #   "cost_current": 45.67,
    #   "cost_limit": 50.00
    # }
    
    # Delivery
    channels_sent = Column(JSON, default=list)  # Which channels it was sent to
    delivery_status = Column(JSON, default=dict)
    # Example:
    # {
    #   "email": {"status": "sent", "sent_at": "2024-12-04T12:00:00"},
    #   "slack": {"status": "failed", "error": "Webhook timeout"}
    # }
    
    # Status
    is_read = Column(Boolean, default=False)  # For in-app notifications
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Grouping (for similar alerts)
    group_key = Column(String(255), nullable=True, index=True)
    is_grouped = Column(Boolean, default=False)
    similar_count = Column(Integer, default=1)  # How many similar alerts grouped
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    alert_config = relationship("AlertConfig", back_populates="notifications")
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class AlertThrottle(Base):
    """Tracks alert throttling to prevent spam."""
    __tablename__ = "alert_throttles"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_config_id = Column(Integer, ForeignKey("alert_configs.id"), nullable=False, index=True)
    
    throttle_key = Column(String(255), nullable=False, index=True)
    # Example: "circuit_breaker_opened:openai"
    
    last_sent_at = Column(DateTime, nullable=False)
    sent_count_this_hour = Column(Integer, default=1)
    hour_started_at = Column(DateTime, default=datetime.utcnow)
    
    next_allowed_at = Column(DateTime, nullable=False)  # Based on cooldown
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alert_config = relationship("AlertConfig", foreign_keys=[alert_config_id])
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class NotificationPreference(Base):
    """User-specific notification preferences."""
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    slack_enabled = Column(Boolean, default=False)
    sms_enabled = Column(Boolean, default=False)
    
    # Contact info
    email_address = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    slack_user_id = Column(String(100), nullable=True)
    
    # Alert type preferences
    alert_type_preferences = Column(JSON, default=dict)
    # Example:
    # {
    #   "circuit_breaker_opened": {"enabled": true, "channels": ["email", "in_app"]},
    #   "cost_limit_warning": {"enabled": true, "channels": ["email"]},
    #   "rate_limit_exceeded": {"enabled": false}
    # }
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), nullable=True)  # "22:00"
    quiet_hours_end = Column(String(5), nullable=True)    # "08:00"
    quiet_hours_timezone = Column(String(50), default="UTC")
    
    # Digest settings
    enable_digest = Column(Boolean, default=False)
    digest_frequency = Column(String(20), default="daily")  # hourly, daily, weekly
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
