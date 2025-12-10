from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from backend.app.db.base import Base


class BudgetScope(str, enum.Enum):
    GLOBAL = "global"
    TENANT = "tenant"
    DEPARTMENT = "department"
    TEAM = "team"
    API_KEY = "api_key"
    USER = "user"
    ROUTE = "route"
    MODEL = "model"


class BudgetPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BudgetPolicy(Base):
    """
    Granular budget policy that can be applied at multiple scopes.
    
    Hierarchy (most specific wins):
    1. Model-specific limit on a route
    2. Route-level limit
    3. API Key / User limit
    4. Team limit
    5. Department limit
    6. Tenant limit
    7. Global limit
    
    Budget is DISABLED by default - enabled flag must be True for enforcement.
    """
    __tablename__ = "budget_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    
    enabled = Column(Boolean, default=False, nullable=False)
    
    scope_type = Column(String(50), nullable=False, index=True)
    scope_id = Column(Integer, nullable=True, index=True)
    
    model_filter = Column(String(100), nullable=True, index=True)
    
    period = Column(String(20), default="monthly", nullable=False)
    
    hard_limit_usd = Column(Float, nullable=True)
    
    soft_threshold_pct = Column(Float, default=80.0)
    warning_threshold_pct = Column(Float, default=90.0)
    critical_threshold_pct = Column(Float, default=95.0)
    
    action_on_limit = Column(String(20), default="block")
    
    alert_recipients = Column(JSON, default=list)
    
    last_alert_sent_at = Column(DateTime, nullable=True)
    alert_cooldown_hours = Column(Integer, default=24)
    
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    metadata_ = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])


class BudgetUsageSnapshot(Base):
    """
    Aggregated usage snapshots for fast budget checking.
    Updated in real-time as usage is logged.
    """
    __tablename__ = "budget_usage_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    policy_id = Column(Integer, ForeignKey("budget_policies.id"), nullable=False, index=True)
    
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    
    total_cost_usd = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)
    request_count = Column(Integer, default=0)
    
    last_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    policy = relationship("BudgetPolicy", foreign_keys=[policy_id])
