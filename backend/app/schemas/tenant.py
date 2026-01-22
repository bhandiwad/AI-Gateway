from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class TenantBase(BaseModel):
    name: str
    email: EmailStr


class TenantCreate(TenantBase):
    password: str


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    rate_limit: Optional[int] = None
    monthly_budget: Optional[float] = None
    allowed_models: Optional[List[str]] = None
    allowed_providers: Optional[List[str]] = None
    guardrail_profile_id: Optional[int] = None
    default_provider_id: Optional[int] = None
    cost_ceiling_daily: Optional[float] = None
    cost_ceiling_monthly: Optional[float] = None
    logging_policy: Optional[Dict[str, Any]] = None


class TenantResponse(TenantBase):
    id: int
    is_active: bool
    is_admin: bool
    rate_limit: int
    monthly_budget: float
    current_spend: float
    allowed_models: Optional[List[str]] = None
    allowed_providers: Optional[List[str]] = None
    guardrail_profile_id: Optional[int] = None
    default_provider_id: Optional[int] = None
    cost_ceiling_daily: Optional[float] = None
    cost_ceiling_monthly: Optional[float] = None
    logging_policy: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant: TenantResponse
