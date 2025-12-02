from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class BillingPeriod(BaseModel):
    start: str
    end: str


class ModelUsage(BaseModel):
    model: str
    provider: str
    requests: int
    prompt_tokens: int
    completion_tokens: int
    cost: float


class UserUsage(BaseModel):
    user_id: int
    name: str
    email: str
    requests: int
    tokens: int
    cost: float


class BillingSummary(BaseModel):
    active_users: int
    total_requests: int
    total_tokens: int
    token_cost: float


class TenantBillingReport(BaseModel):
    tenant_id: int
    tenant_name: str
    billing_period: BillingPeriod
    summary: BillingSummary
    by_model: List[ModelUsage]
    by_user: List[UserUsage]


class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: Optional[float]
    amount: float


class Invoice(BaseModel):
    invoice_number: str
    tenant_id: int
    tenant_name: str
    billing_period: BillingPeriod
    generated_at: str
    line_items: List[LineItem]
    model_breakdown: List[Dict[str, Any]]
    subtotal: float
    tax_rate: float
    tax: float
    total: float
    currency: str


class CostForecast(BaseModel):
    current_daily_average: float
    projected_cost: float
    days_to_forecast: int
    active_users: int
    monthly_budget: float
    budget_utilization_forecast: float
    will_exceed_budget: bool


class BillingReportRequest(BaseModel):
    start_date: datetime
    end_date: datetime


class InvoiceRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    user_rate: float = 10.0
    include_token_costs: bool = True
