from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from backend.app.db.session import Base


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    API_REQUEST = "api_request"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    TENANT_UPDATED = "tenant_updated"
    POLICY_CHANGED = "policy_changed"
    GUARDRAIL_TRIGGERED = "guardrail_triggered"
    BUDGET_EXCEEDED = "budget_exceeded"
    RATE_LIMIT_HIT = "rate_limit_hit"
    SSO_LOGIN = "sso_login"
    CONFIG_CHANGED = "config_changed"
    DATA_EXPORT = "data_export"
    ADMIN_ACTION = "admin_action"


class AuditSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    severity = Column(SQLEnum(AuditSeverity), default=AuditSeverity.INFO)
    
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    
    description = Column(Text, nullable=True)
    
    request_id = Column(String(64), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    metadata_ = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    tenant = relationship("Tenant")
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
