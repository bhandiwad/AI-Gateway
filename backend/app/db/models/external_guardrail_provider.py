from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.app.db.session import Base


class ExternalGuardrailProvider(Base):
    """External third-party guardrail provider configuration."""
    __tablename__ = "external_guardrail_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    provider_type = Column(String(50), nullable=False)  # openai, aws_comprehend, google_nlp, azure_content_safety
    description = Column(Text, nullable=True)
    
    is_enabled = Column(Boolean, default=True)
    is_global = Column(Boolean, default=False)  # Available to all tenants
    
    # API configuration
    api_key_encrypted = Column(Text, nullable=True)  # Store encrypted
    api_endpoint = Column(String(500), nullable=True)
    region = Column(String(50), nullable=True)
    
    # Provider settings
    timeout_seconds = Column(Integer, default=10)
    retry_attempts = Column(Integer, default=2)
    priority = Column(Integer, default=100)  # Lower = higher priority
    
    # Category thresholds
    thresholds = Column(JSON, default=lambda: {
        "toxicity": 0.7,
        "hate_speech": 0.7,
        "violence": 0.7,
        "sexual": 0.7,
        "self_harm": 0.7
    })
    
    # Custom configuration
    custom_config = Column(JSON, default=dict)
    
    # Capabilities
    capabilities = Column(JSON, default=list)  # List of supported categories
    
    # Health and metrics
    last_health_check = Column(DateTime, nullable=True)
    is_healthy = Column(Boolean, default=True)
    total_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    avg_latency_ms = Column(Integer, nullable=True)
    
    metadata_ = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
