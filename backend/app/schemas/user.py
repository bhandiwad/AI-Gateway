from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: Optional[str] = None
    role: UserRole = UserRole.USER
    allowed_models: Optional[List[str]] = None
    rate_limit: int = 60
    monthly_budget: int = 100


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    allowed_models: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    monthly_budget: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    tenant_id: int
    email: str
    name: str
    role: str
    status: str
    allowed_models: List[str]
    rate_limit: int
    monthly_budget: int
    current_spend: int
    last_login_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class UserUsageSummary(BaseModel):
    user_id: int
    total_requests: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float
    by_model: Dict[str, Any]
