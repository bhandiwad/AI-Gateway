from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.app.db.session import Base


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(20), nullable=False)
    
    is_active = Column(Boolean, default=True)
    
    environment = Column(String(20), default="production")
    
    guardrail_profile_id = Column(Integer, ForeignKey("guardrail_profiles.id"), nullable=True)
    default_provider_id = Column(Integer, ForeignKey("provider_configs_v2.id"), nullable=True)
    
    rate_limit_override = Column(Integer, nullable=True)
    allowed_models_override = Column(JSON, nullable=True)
    allowed_providers_override = Column(JSON, nullable=True)
    
    cost_limit_daily = Column(Integer, nullable=True)
    cost_limit_monthly = Column(Integer, nullable=True)
    
    metadata_ = Column("metadata", JSON, default=dict)
    
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="api_keys")
    guardrail_profile = relationship("GuardrailProfile", foreign_keys=[guardrail_profile_id])
    default_provider = relationship("EnhancedProviderConfig", foreign_keys=[default_provider_id])
