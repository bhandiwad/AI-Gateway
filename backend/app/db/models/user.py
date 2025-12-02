from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from backend.app.db.session import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    email = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)
    
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    
    sso_provider = Column(String(100), nullable=True)
    sso_user_id = Column(String(255), nullable=True)
    
    allowed_models = Column(JSON, default=list)
    rate_limit = Column(Integer, default=60)
    monthly_budget = Column(Integer, default=100)
    current_spend = Column(Integer, default=0)
    
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    metadata_ = Column("metadata", JSON, default=dict)
    
    tenant = relationship("Tenant", back_populates="users")
    usage_logs = relationship("UsageLog", back_populates="user", foreign_keys="UsageLog.user_id")
    audit_logs = relationship("AuditLog", back_populates="user")

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
