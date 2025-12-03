from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.app.db.session import Base


class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    rate_limit = Column(Integer, default=100)
    monthly_budget = Column(Float, default=100.0)
    current_spend = Column(Float, default=0.0)
    
    guardrail_policy = Column(String(50), default="default")
    
    guardrail_profile_id = Column(Integer, ForeignKey("guardrail_profiles.id"), nullable=True)
    default_provider_id = Column(Integer, ForeignKey("provider_configs_v2.id"), nullable=True)
    
    cost_ceiling_daily = Column(Float, nullable=True)
    cost_ceiling_monthly = Column(Float, nullable=True)
    
    logging_policy = Column(JSON, default=lambda: {
        "log_requests": True,
        "log_responses": True,
        "log_pii_detected": True,
        "log_guardrail_triggers": True,
        "retention_days": 90
    })
    
    allowed_providers = Column(JSON, default=list)
    
    allowed_models = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    api_keys = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    sso_config = relationship("SSOConfig", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    guardrail_profile = relationship("GuardrailProfile", foreign_keys=[guardrail_profile_id])
    default_provider = relationship("EnhancedProviderConfig", foreign_keys=[default_provider_id])
