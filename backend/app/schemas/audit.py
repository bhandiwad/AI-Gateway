from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AuditAction(str, Enum):
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


class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogResponse(BaseModel):
    id: int
    tenant_id: int
    user_id: Optional[int]
    action: str
    severity: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    description: Optional[str]
    request_id: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class AuditSummary(BaseModel):
    total_events: int
    security_events: int
    by_action: Dict[str, int]
    by_severity: Dict[str, int]


class AuditExportRequest(BaseModel):
    start_date: datetime
    end_date: datetime


class AuditExportResponse(BaseModel):
    logs: List[Dict[str, Any]]
    total_count: int
    export_date: datetime
