from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, UniqueConstraint
from datetime import datetime

from backend.app.db.session import Base


class CustomModel(Base):
    __tablename__ = "custom_models"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    model_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False)
    
    context_length = Column(Integer, default=128000)
    input_cost_per_1k = Column(Float, default=0.0)
    output_cost_per_1k = Column(Float, default=0.0)
    
    supports_streaming = Column(Boolean, default=True)
    supports_functions = Column(Boolean, default=False)
    supports_vision = Column(Boolean, default=False)
    
    api_base_url = Column(String(500), nullable=True)
    api_key_name = Column(String(100), nullable=True)
    
    is_enabled = Column(Boolean, default=True)
    display_order = Column(Integer, default=1000)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'model_id', name='uq_custom_tenant_model'),
    )
