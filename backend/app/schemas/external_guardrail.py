from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ExternalGuardrailProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    provider_type: str = Field(..., pattern="^(openai|aws_comprehend|google_nlp|azure_content_safety|custom)$")
    description: Optional[str] = None
    api_endpoint: Optional[str] = None
    region: Optional[str] = None
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    retry_attempts: int = Field(default=2, ge=0, le=5)
    priority: int = Field(default=100, ge=0)
    thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "toxicity": 0.7,
        "hate_speech": 0.7,
        "violence": 0.7,
        "sexual": 0.7,
        "self_harm": 0.7
    })
    custom_config: Dict[str, Any] = Field(default_factory=dict)


class ExternalGuardrailProviderCreate(ExternalGuardrailProviderBase):
    api_key: Optional[str] = Field(None, description="API key for the provider (will be encrypted)")
    is_global: bool = False


class ExternalGuardrailProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    api_key: Optional[str] = None
    api_endpoint: Optional[str] = None
    region: Optional[str] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=60)
    retry_attempts: Optional[int] = Field(None, ge=0, le=5)
    priority: Optional[int] = Field(None, ge=0)
    thresholds: Optional[Dict[str, float]] = None
    custom_config: Optional[Dict[str, Any]] = None


class ExternalGuardrailProviderResponse(ExternalGuardrailProviderBase):
    id: int
    tenant_id: Optional[int]
    is_enabled: bool
    is_global: bool
    capabilities: List[str]
    last_health_check: Optional[datetime]
    is_healthy: bool
    total_requests: int
    failed_requests: int
    avg_latency_ms: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GuardrailCheckRequest(BaseModel):
    text: str = Field(..., min_length=1)
    stage: str = Field("input", pattern="^(input|output)$")
    providers: Optional[List[str]] = Field(None, description="Specific providers to use")
    context: Optional[Dict[str, Any]] = None


class GuardrailCheckResponse(BaseModel):
    provider: str
    passed: bool
    violations: List[Dict[str, Any]]
    recommended_action: str
    processing_time_ms: float
    metadata: Dict[str, Any] = {}


class ProviderHealthResponse(BaseModel):
    provider_name: str
    is_healthy: bool
    last_check: Optional[datetime]
    capabilities: List[str]
