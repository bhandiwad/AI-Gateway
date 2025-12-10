from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.app.db.session import Base


class Department(Base):
    """Department for organizational structure (top-level)."""
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    cost_center = Column(String(100), nullable=True)
    
    budget_monthly = Column(Float, nullable=True)
    budget_yearly = Column(Float, nullable=True)
    current_spend = Column(Float, default=0.0)
    
    manager_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    guardrail_profile_id = Column(Integer, ForeignKey("guardrail_profiles.id"), nullable=True)
    allowed_models = Column(JSON, default=list)
    allowed_providers = Column(JSON, default=list)
    
    metadata_ = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    manager = relationship("User", foreign_keys=[manager_user_id])
    guardrail_profile = relationship("GuardrailProfile", foreign_keys=[guardrail_profile_id])
    teams = relationship("Team", back_populates="department", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="department")
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
