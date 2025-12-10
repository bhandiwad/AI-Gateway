"""
Budget Management API Routes

Provides endpoints for managing granular budget policies at multiple levels.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.db.session import get_db
from backend.app.api.v1.routes_auth import get_current_user_from_token
from backend.app.services.budget_enforcement_service import BudgetEnforcementService

router = APIRouter(prefix="/budget", tags=["Budget Management"])


class BudgetPolicyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scope_type: str = Field(..., description="Scope type: tenant, department, team, api_key, user, route, model, global")
    scope_id: Optional[int] = None
    model_filter: Optional[str] = Field(None, description="Optional model name to filter (e.g., gpt-4)")
    period: str = Field("monthly", description="Budget period: daily, weekly, monthly, quarterly, yearly")
    hard_limit_usd: Optional[float] = Field(None, ge=0, description="Hard spending limit in USD")
    action_on_limit: str = Field("block", description="Action when limit reached: block or warn")
    enabled: bool = Field(False, description="Whether budget is enabled (disabled by default)")
    soft_threshold_pct: float = Field(80.0, ge=0, le=100)
    warning_threshold_pct: float = Field(90.0, ge=0, le=100)
    critical_threshold_pct: float = Field(95.0, ge=0, le=100)
    alert_recipients: List[str] = Field(default_factory=list)


class BudgetPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_filter: Optional[str] = None
    period: Optional[str] = None
    hard_limit_usd: Optional[float] = None
    action_on_limit: Optional[str] = None
    enabled: Optional[bool] = None
    soft_threshold_pct: Optional[float] = None
    warning_threshold_pct: Optional[float] = None
    critical_threshold_pct: Optional[float] = None
    alert_recipients: Optional[List[str]] = None


class BudgetCheckRequest(BaseModel):
    model: str
    estimated_cost: float = 0.0
    api_key_id: Optional[int] = None
    user_id: Optional[int] = None
    team_id: Optional[int] = None
    department_id: Optional[int] = None
    route_id: Optional[int] = None


@router.get("/policies")
async def list_budget_policies(
    scope_type: Optional[str] = None,
    scope_id: Optional[int] = None,
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List all budget policies for the current tenant."""
    service = BudgetEnforcementService(db)
    policies = service.get_budget_summary(
        tenant_id=current_user.tenant_id,
        scope_type=scope_type,
        scope_id=scope_id
    )
    return {"policies": policies, "count": len(policies)}


@router.post("/policies")
async def create_budget_policy(
    policy: BudgetPolicyCreate,
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new budget policy (disabled by default)."""
    service = BudgetEnforcementService(db)
    
    valid_scopes = ["tenant", "department", "team", "api_key", "user", "route", "model", "global"]
    if policy.scope_type not in valid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope_type. Must be one of: {valid_scopes}"
        )
    
    valid_periods = ["daily", "weekly", "monthly", "quarterly", "yearly"]
    if policy.period not in valid_periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period. Must be one of: {valid_periods}"
        )
    
    new_policy = service.create_policy(
        tenant_id=current_user.tenant_id,
        name=policy.name,
        scope_type=policy.scope_type,
        scope_id=policy.scope_id,
        model_filter=policy.model_filter,
        period=policy.period,
        hard_limit_usd=policy.hard_limit_usd,
        action_on_limit=policy.action_on_limit,
        enabled=policy.enabled,
        created_by_user_id=current_user.id,
        soft_threshold_pct=policy.soft_threshold_pct,
        warning_threshold_pct=policy.warning_threshold_pct,
        critical_threshold_pct=policy.critical_threshold_pct,
        alert_recipients=policy.alert_recipients,
        description=policy.description
    )
    
    return {
        "message": "Budget policy created successfully",
        "policy": {
            "id": new_policy.id,
            "name": new_policy.name,
            "enabled": new_policy.enabled,
            "scope_type": new_policy.scope_type
        }
    }


@router.put("/policies/{policy_id}")
async def update_budget_policy(
    policy_id: int,
    updates: BudgetPolicyUpdate,
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update an existing budget policy."""
    service = BudgetEnforcementService(db)
    
    update_dict = updates.model_dump(exclude_none=True)
    
    updated_policy = service.update_policy(
        policy_id=policy_id,
        tenant_id=current_user.tenant_id,
        **update_dict
    )
    
    if not updated_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget policy not found"
        )
    
    return {
        "message": "Budget policy updated successfully",
        "policy": {
            "id": updated_policy.id,
            "name": updated_policy.name,
            "enabled": updated_policy.enabled
        }
    }


@router.delete("/policies/{policy_id}")
async def delete_budget_policy(
    policy_id: int,
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a budget policy."""
    service = BudgetEnforcementService(db)
    
    success = service.delete_policy(
        policy_id=policy_id,
        tenant_id=current_user.tenant_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget policy not found"
        )
    
    return {"message": "Budget policy deleted successfully"}


@router.post("/policies/{policy_id}/toggle")
async def toggle_budget_policy(
    policy_id: int,
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Toggle a budget policy on/off."""
    service = BudgetEnforcementService(db)
    
    from backend.app.db.models import BudgetPolicy
    policy = db.query(BudgetPolicy).filter(
        BudgetPolicy.id == policy_id,
        BudgetPolicy.tenant_id == current_user.tenant_id
    ).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget policy not found"
        )
    
    new_state = not policy.enabled
    service.update_policy(policy_id, current_user.tenant_id, enabled=new_state)
    
    return {
        "message": f"Budget policy {'enabled' if new_state else 'disabled'}",
        "policy_id": policy_id,
        "enabled": new_state
    }


@router.post("/check")
async def check_budget(
    request: BudgetCheckRequest,
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Check if a request would be allowed under current budget policies."""
    service = BudgetEnforcementService(db)
    
    result = service.check_budget(
        tenant_id=current_user.tenant_id,
        model=request.model,
        estimated_cost=request.estimated_cost,
        api_key_id=request.api_key_id,
        user_id=request.user_id,
        team_id=request.team_id,
        department_id=request.department_id,
        route_id=request.route_id
    )
    
    return result.to_dict()


@router.get("/scope-options")
async def get_scope_options(
    current_user = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get available scope options for budget policies."""
    from backend.app.db.models import Department, Team, APIKey, User
    from backend.app.db.models.provider_config import APIRoute
    
    departments = db.query(Department).filter(
        Department.tenant_id == current_user.tenant_id
    ).all()
    
    teams = db.query(Team).filter(
        Team.tenant_id == current_user.tenant_id
    ).all()
    
    api_keys = db.query(APIKey).filter(
        APIKey.tenant_id == current_user.tenant_id
    ).all()
    
    users = db.query(User).filter(
        User.tenant_id == current_user.tenant_id
    ).all()
    
    routes = db.query(APIRoute).filter(
        APIRoute.tenant_id == current_user.tenant_id
    ).all()
    
    return {
        "scopes": [
            {"type": "tenant", "name": "Organization-wide", "description": "Apply to entire organization"},
            {"type": "department", "name": "Department", "description": "Apply to specific department", 
             "options": [{"id": d.id, "name": d.name} for d in departments]},
            {"type": "team", "name": "Team", "description": "Apply to specific team",
             "options": [{"id": t.id, "name": t.name} for t in teams]},
            {"type": "api_key", "name": "API Key", "description": "Apply to specific API key",
             "options": [{"id": k.id, "name": k.name} for k in api_keys]},
            {"type": "user", "name": "User", "description": "Apply to specific user",
             "options": [{"id": u.id, "name": u.name} for u in users]},
            {"type": "route", "name": "API Route", "description": "Apply to specific API route",
             "options": [{"id": r.id, "name": r.path} for r in routes]},
            {"type": "model", "name": "Model", "description": "Apply to specific AI model"}
        ],
        "periods": [
            {"id": "daily", "name": "Daily"},
            {"id": "weekly", "name": "Weekly"},
            {"id": "monthly", "name": "Monthly"},
            {"id": "quarterly", "name": "Quarterly"},
            {"id": "yearly", "name": "Yearly"}
        ],
        "actions": [
            {"id": "block", "name": "Block", "description": "Block requests when limit is reached"},
            {"id": "warn", "name": "Warn", "description": "Log warning but allow requests"}
        ]
    }
