from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.app.db.session import Base


class EnhancedProviderConfig(Base):
    """Enhanced provider configuration matching F5 AI Gateway capabilities."""
    __tablename__ = "provider_configs_v2"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    name = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    service_type = Column(String(50), nullable=False)
    
    endpoint_url = Column(String(500), nullable=True)
    api_key_secret_name = Column(String(100), nullable=True)
    
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    timeout_seconds = Column(Integer, default=120)
    max_retries = Column(Integer, default=3)
    
    traffic_leaves_enterprise = Column(Boolean, default=True)
    
    models = Column(JSON, default=list)
    
    rate_limit_rpm = Column(Integer, nullable=True)
    rate_limit_tpm = Column(Integer, nullable=True)
    
    config = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    provider_models = relationship("ProviderModel", back_populates="provider", cascade="all, delete-orphan")


class ProviderModel(Base):
    """Individual model configuration for a provider."""
    __tablename__ = "provider_models"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("provider_configs_v2.id"), nullable=False)
    
    model_id = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    context_length = Column(Integer, nullable=True)
    input_cost_per_1k = Column(Float, nullable=True)
    output_cost_per_1k = Column(Float, nullable=True)
    
    capabilities = Column(JSON, default=list)
    
    config = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    provider = relationship("EnhancedProviderConfig", back_populates="provider_models")


class APIRoute(Base):
    """API route configuration with per-route policies and limits."""
    __tablename__ = "api_routes"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    path = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    policy_id = Column(Integer, ForeignKey("routing_policies.id"), nullable=True)
    
    default_provider_id = Column(Integer, ForeignKey("provider_configs_v2.id"), nullable=True)
    default_model = Column(String(100), nullable=True)
    
    allowed_methods = Column(JSON, default=lambda: ["POST"])
    
    request_size_limit_kb = Column(Integer, default=10240)
    timeout_seconds = Column(Integer, default=120)
    
    rate_limit_rpm = Column(Integer, nullable=True)
    
    config = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    policy = relationship("RoutingPolicy", foreign_keys=[policy_id])
    default_provider = relationship("EnhancedProviderConfig", foreign_keys=[default_provider_id])


class RoutingPolicy(Base):
    """Routing policy that maps tenant/profile to processors and services."""
    __tablename__ = "routing_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    selectors = Column(JSON, default=dict)
    
    profile_id = Column(Integer, ForeignKey("guardrail_profiles.id"), nullable=True)
    
    allowed_providers = Column(JSON, default=list)
    allowed_models = Column(JSON, default=list)
    
    config = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    profile = relationship("GuardrailProfile", foreign_keys=[profile_id])


class GuardrailProfile(Base):
    """Guardrail profile with ordered request/response processors."""
    __tablename__ = "guardrail_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    request_processors = Column(JSON, default=list)
    response_processors = Column(JSON, default=list)
    
    logging_level = Column(String(20), default="info")
    
    config = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", foreign_keys=[tenant_id])


class ProcessorDefinition(Base):
    """Definition of available guardrail processors."""
    __tablename__ = "processor_definitions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    processor_type = Column(String(50), nullable=False)
    stage = Column(String(20), nullable=False)
    
    is_active = Column(Boolean, default=True)
    is_builtin = Column(Boolean, default=True)
    
    default_config = Column(JSON, default=dict)
    
    supported_actions = Column(JSON, default=lambda: ["block", "allow", "rewrite", "warn"])
    
    created_at = Column(DateTime, default=datetime.utcnow)
