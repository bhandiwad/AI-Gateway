from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.app.db.session import Base


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
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
    
    cost_limit_daily = Column(Float, nullable=True)
    cost_limit_monthly = Column(Float, nullable=True)
    
    tags = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)
    
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="api_keys")
    department = relationship("Department", back_populates="api_keys")
    team = relationship("Team", back_populates="api_keys")
    owner = relationship("User", foreign_keys=[owner_user_id])
    guardrail_profile = relationship("GuardrailProfile", foreign_keys=[guardrail_profile_id])
    default_provider = relationship("EnhancedProviderConfig", foreign_keys=[default_provider_id])
