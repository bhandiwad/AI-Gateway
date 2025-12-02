from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class APIKeyCreate(BaseModel):
    name: str
    rate_limit_override: Optional[int] = None
    allowed_models_override: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    key_prefix: str
    is_active: bool
    rate_limit_override: Optional[int]
    allowed_models_override: Optional[List[str]]
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    api_key: str
