from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.app.db.session import Base


class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    
    request_id = Column(String(64), unique=True, nullable=False, index=True)
    
    endpoint = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    cost = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    
    status = Column(String(20), default="success")
    error_message = Column(Text, nullable=True)
    
    request_metadata = Column(JSON, default=dict)
    response_metadata = Column(JSON, default=dict)
    
    guardrail_triggered = Column(String(100), nullable=True)
    guardrail_action = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    tenant = relationship("Tenant", back_populates="usage_logs")
    user = relationship("User", back_populates="usage_logs", foreign_keys=[user_id])
    department = relationship("Department", foreign_keys=[department_id])
    team = relationship("Team", foreign_keys=[team_id])
