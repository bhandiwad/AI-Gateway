from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class APIKeyCreate(BaseModel):
    name: str
    environment: Optional[str] = "production"
    guardrail_profile_id: Optional[int] = None
    default_provider_id: Optional[int] = None
    rate_limit_override: Optional[int] = None
    allowed_models_override: Optional[List[str]] = None
    allowed_providers_override: Optional[List[str]] = None
    cost_limit_daily: Optional[float] = None
    cost_limit_monthly: Optional[float] = None
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    key_prefix: str
    is_active: bool
    environment: Optional[str] = "production"
    guardrail_profile_id: Optional[int] = None
    default_provider_id: Optional[int] = None
    rate_limit_override: Optional[int] = None
    allowed_models_override: Optional[List[str]] = None
    allowed_providers_override: Optional[List[str]] = None
    cost_limit_daily: Optional[float] = None
    cost_limit_monthly: Optional[float] = None
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    api_key: str
