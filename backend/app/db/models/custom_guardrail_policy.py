from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, ForeignKey
from datetime import datetime

from backend.app.db.session import Base


class CustomGuardrailPolicy(Base):
    __tablename__ = "custom_guardrail_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    policy_type = Column(String(50), nullable=False, default="custom")
    
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    
    config = Column(JSON, default=dict)
    
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
