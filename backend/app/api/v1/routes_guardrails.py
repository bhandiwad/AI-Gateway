from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from backend.app.db.session import get_db
from backend.app.core.security import get_current_tenant
from backend.app.db.models.tenant import Tenant
from backend.app.services.nemo_guardrails_service import nemo_guardrails_service

router = APIRouter()


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
    tenant: Tenant = Depends(get_current_tenant)
):
    return {
        "guardrails": nemo_guardrails_service.get_available_guardrails(),
        "policies": nemo_guardrails_service.get_policy_templates(),
        "current_policy": tenant.guardrail_policy if hasattr(tenant, 'guardrail_policy') else "default"
    }


@router.get("/guardrails/policies")
async def list_policies():
    return {
        "policies": nemo_guardrails_service.get_policy_templates()
    }


@router.post("/guardrails/test", response_model=GuardrailTestResponse)
async def test_guardrails(
    request: GuardrailTestRequest,
    tenant: Tenant = Depends(get_current_tenant),
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
async def get_bfsi_guardrails():
    all_guardrails = nemo_guardrails_service.get_available_guardrails()
    bfsi_guardrails = [g for g in all_guardrails if g.get("bfsi_relevant", False)]
    
    return {
        "guardrails": bfsi_guardrails,
        "recommended_policy": "bfsi",
        "description": "BFSI-specific guardrails for banking, financial services, and insurance compliance"
    }


@router.put("/guardrails/policy")
async def update_policy(
    policy: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    valid_policies = ["default", "strict", "bfsi", "permissive"]
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
