from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class PolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    policy_type: str
    is_active: bool = True
    priority: int = 0
    config: Dict[str, Any] = {}


class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class PolicyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    policy_type: str
    is_active: bool
    priority: int
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProviderConfigCreate(BaseModel):
    name: str
    provider_type: str
    is_active: bool = True
    priority: int = 0
    api_base: Optional[str] = None
    api_key_env: Optional[str] = None
    models: List[str] = []
    config: Dict[str, Any] = {}


class ProviderConfigResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    is_active: bool
    priority: int
    api_base: Optional[str]
    api_key_env: Optional[str]
    models: List[str]
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    context_length: int
    input_cost_per_token: float
    output_cost_per_token: float
    supports_streaming: bool
    supports_functions: bool
    supports_vision: bool
