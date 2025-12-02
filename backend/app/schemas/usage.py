from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class UsageLogResponse(BaseModel):
    id: int
    tenant_id: int
    request_id: str
    endpoint: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    latency_ms: int
    status: str
    error_message: Optional[str]
    guardrail_triggered: Optional[str]
    guardrail_action: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UsageSummary(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float
    success_rate: float
    by_model: Dict[str, Dict[str, Any]]
    by_provider: Dict[str, Dict[str, Any]]


class UsageTimeSeries(BaseModel):
    timestamp: datetime
    requests: int
    tokens: int
    cost: float


class DashboardStats(BaseModel):
    period: str
    total_requests: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float
    success_rate: float
    top_models: List[Dict[str, Any]]
    usage_over_time: List[UsageTimeSeries]
