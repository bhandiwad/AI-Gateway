from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    cost_center: Optional[str] = Field(None, max_length=100)
    budget_monthly: Optional[float] = Field(None, ge=0)
    budget_yearly: Optional[float] = Field(None, ge=0)
    manager_user_id: Optional[int] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    cost_center: Optional[str] = Field(None, max_length=100)
    budget_monthly: Optional[float] = Field(None, ge=0)
    budget_yearly: Optional[float] = Field(None, ge=0)
    manager_user_id: Optional[int] = None


class DepartmentResponse(DepartmentBase):
    id: int
    tenant_id: int
    is_active: bool
    current_spend: float
    created_at: datetime
    updated_at: datetime
    metadata_: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class DepartmentWithStats(DepartmentResponse):
    team_count: int = 0
    user_count: int = 0
    api_key_count: int = 0
    monthly_spend: float = 0.0
    budget_utilization: float = 0.0


class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    department_id: Optional[int] = None
    budget_monthly: Optional[float] = Field(None, ge=0)
    lead_user_id: Optional[int] = None
    tags: List[str] = []


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    department_id: Optional[int] = None
    budget_monthly: Optional[float] = Field(None, ge=0)
    lead_user_id: Optional[int] = None
    tags: Optional[List[str]] = None


class TeamResponse(TeamBase):
    id: int
    tenant_id: int
    is_active: bool
    current_spend: float
    created_at: datetime
    updated_at: datetime
    metadata_: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True


class TeamWithStats(TeamResponse):
    member_count: int = 0
    api_key_count: int = 0
    monthly_spend: float = 0.0
    budget_utilization: float = 0.0


class TeamMemberAdd(BaseModel):
    user_id: int
    role: str = Field(default="member", pattern="^(member|lead)$")


class TeamMemberRemove(BaseModel):
    user_id: int


class OrganizationStats(BaseModel):
    total_departments: int
    total_teams: int
    total_users: int
    total_api_keys: int
    total_spend_month: float
    total_budget_month: float
    budget_utilization: float
    top_departments_by_spend: List[Dict[str, Any]] = []
    top_teams_by_spend: List[Dict[str, Any]] = []
