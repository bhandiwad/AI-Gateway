from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from backend.app.db.session import get_db
from backend.app.core.security import get_current_tenant, get_current_user
from backend.app.core.permissions import Permission, RequirePermission
from backend.app.db.models.tenant import Tenant
from backend.app.services.nemo_guardrails_service import nemo_guardrails_service
from backend.app.services.custom_policy_service import custom_policy_service

router = APIRouter()


class PolicyCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    config: Optional[dict] = None
    is_active: bool = True


class PolicyUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class GuardrailTestRequest(BaseModel):
    text: str
    policy: str = "default"
    is_input: bool = True
    allowed_topics: Optional[List[str]] = None


class GuardrailTestResponse(BaseModel):
    original_text: str
    processed_text: str
    blocked: bool
    warnings: List[str]
    triggered_guardrails: List[dict]
    actions_taken: List[str]


@router.get("/guardrails")
async def list_guardrails(
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return {
        "guardrails": nemo_guardrails_service.get_available_guardrails(),
        "policies": nemo_guardrails_service.get_policy_templates(),
        "current_policy": tenant.guardrail_policy if hasattr(tenant, 'guardrail_policy') else "default"
    }


@router.get("/guardrails/policies")
async def list_policies(
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_VIEW))
):
    return {
        "policies": nemo_guardrails_service.get_policy_templates()
    }


@router.post("/guardrails/test", response_model=GuardrailTestResponse)
async def test_guardrails(
    request: GuardrailTestRequest,
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_TEST)),
    db: Session = Depends(get_db)
):
    result = nemo_guardrails_service.apply_guardrails(
        text=request.text,
        policy=request.policy,
        is_input=request.is_input,
        allowed_topics=request.allowed_topics
    )
    
    return GuardrailTestResponse(
        original_text=result["original_text"],
        processed_text=result["processed_text"],
        blocked=result["blocked"],
        warnings=result["warnings"],
        triggered_guardrails=result["triggered_guardrails"],
        actions_taken=result["actions_taken"]
    )


@router.get("/guardrails/bfsi")
async def get_compliance_guardrails(
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_VIEW))
):
    all_guardrails = nemo_guardrails_service.get_available_guardrails()
    compliance_guardrails = [g for g in all_guardrails if g.get("bfsi_relevant", False)]
    
    return {
        "guardrails": compliance_guardrails,
        "recommended_policy": "compliance",
        "description": "Enterprise compliance guardrails for regulated industries"
    }


@router.put("/guardrails/policy")
async def update_policy(
    policy: str,
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_EDIT)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    valid_policies = ["default", "strict", "compliance", "permissive"]
    if policy not in valid_policies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy. Choose from: {', '.join(valid_policies)}"
        )
    
    if hasattr(tenant, 'guardrail_policy'):
        tenant.guardrail_policy = policy
        db.commit()
    
    return {
        "success": True,
        "policy": policy,
        "message": f"Guardrail policy updated to '{policy}'"
    }


@router.get("/guardrails/custom")
async def list_custom_policies(
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_VIEW)),
    db: Session = Depends(get_db)
):
    """List all custom policies for this tenant"""
    tenant_id = int(current_user["sub"])
    policies = custom_policy_service.get_tenant_policies(db, tenant_id)
    return {"policies": policies}


@router.get("/guardrails/custom/{policy_id}")
async def get_custom_policy(
    policy_id: int,
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_VIEW)),
    db: Session = Depends(get_db)
):
    """Get a specific custom policy"""
    tenant_id = int(current_user["sub"])
    policy = custom_policy_service.get_policy_by_id(db, tenant_id, policy_id)
    
    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Policy not found"
        )
    
    return policy


@router.post("/guardrails/custom")
async def create_custom_policy(
    request: PolicyCreateRequest,
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_EDIT)),
    db: Session = Depends(get_db)
):
    """Create a new custom policy"""
    tenant_id = int(current_user["sub"])
    user_id = current_user.get("user_id")
    
    policy = custom_policy_service.create_policy(
        db=db,
        tenant_id=tenant_id,
        name=request.name,
        description=request.description,
        config=request.config,
        is_active=request.is_active,
        created_by=user_id
    )
    
    return policy


@router.put("/guardrails/custom/{policy_id}")
async def update_custom_policy(
    policy_id: int,
    request: PolicyUpdateRequest,
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_EDIT)),
    db: Session = Depends(get_db)
):
    """Update a custom policy"""
    tenant_id = int(current_user["sub"])
    
    policy = custom_policy_service.update_policy(
        db=db,
        tenant_id=tenant_id,
        policy_id=policy_id,
        name=request.name,
        description=request.description,
        config=request.config,
        is_active=request.is_active
    )
    
    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Policy not found"
        )
    
    return policy


@router.delete("/guardrails/custom/{policy_id}")
async def delete_custom_policy(
    policy_id: int,
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_EDIT)),
    db: Session = Depends(get_db)
):
    """Delete a custom policy"""
    tenant_id = int(current_user["sub"])
    
    success = custom_policy_service.delete_policy(db, tenant_id, policy_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Policy not found"
        )
    
    return {"success": True, "message": "Policy deleted successfully"}


@router.post("/guardrails/custom/{policy_id}/activate")
async def activate_custom_policy(
    policy_id: int,
    current_user: dict = Depends(RequirePermission(Permission.GUARDRAILS_EDIT)),
    db: Session = Depends(get_db)
):
    """Set a custom policy as the default for this tenant"""
    tenant_id = int(current_user["sub"])
    
    policy = custom_policy_service.set_default_policy(db, tenant_id, policy_id)
    
    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Policy not found"
        )
    
    return {"success": True, "policy": policy, "message": "Policy activated as default"}
