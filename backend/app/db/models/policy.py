from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from datetime import datetime

from backend.app.db.session import Base


class Policy(Base):
    __tablename__ = "policies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    policy_type = Column(String(50), nullable=False)
    
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    config = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProviderConfig(Base):
    __tablename__ = "provider_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(100), unique=True, nullable=False)
    provider_type = Column(String(50), nullable=False)
    
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    api_base = Column(String(500), nullable=True)
    api_key_env = Column(String(100), nullable=True)
    
    models = Column(JSON, default=list)
    config = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
