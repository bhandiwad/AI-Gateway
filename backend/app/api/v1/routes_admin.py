from typing import Optional, List
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.core.security import create_access_token, get_current_user
from backend.app.services.tenancy_service import tenancy_service
from backend.app.services.usage_service import usage_service
from backend.app.services.router_service import router_service
from backend.app.schemas.tenant import (
    TenantCreate, TenantUpdate, TenantResponse, 
    TenantLogin, TokenResponse
)
from backend.app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyCreatedResponse
from backend.app.schemas.usage import UsageSummary, DashboardStats
from backend.app.schemas.policy import ModelInfo

router = APIRouter()


@router.post("/auth/register", response_model=TokenResponse)
async def register(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db)
):
    existing = tenancy_service.get_tenant_by_email(db, tenant_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    tenant = tenancy_service.create_tenant(db, tenant_data)
    
    access_token = create_access_token(
        data={"sub": str(tenant.id), "email": tenant.email, "is_admin": tenant.is_admin}
    )
    
    return TokenResponse(
        access_token=access_token,
        tenant=TenantResponse.model_validate(tenant)
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    credentials: TenantLogin,
    db: Session = Depends(get_db)
):
    tenant = tenancy_service.authenticate_tenant(
        db, credentials.email, credentials.password
    )
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(
        data={"sub": str(tenant.id), "email": tenant.email, "is_admin": tenant.is_admin}
    )
    
    return TokenResponse(
        access_token=access_token,
        tenant=TenantResponse.model_validate(tenant)
    )


@router.get("/auth/me", response_model=TenantResponse)
async def get_current_tenant(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant = tenancy_service.get_tenant_by_id(db, int(current_user["sub"]))
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return TenantResponse.model_validate(tenant)


@router.get("/tenants", response_model=List[TenantResponse])
async def list_tenants(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    tenants = tenancy_service.get_tenants(db, skip, limit)
    return [TenantResponse.model_validate(t) for t in tenants]


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.get("is_admin") and int(current_user["sub"]) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    tenant = tenancy_service.get_tenant_by_id(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return TenantResponse.model_validate(tenant)


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_update: TenantUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.get("is_admin") and int(current_user["sub"]) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    tenant = tenancy_service.update_tenant(db, tenant_id, tenant_update)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    return TenantResponse.model_validate(tenant)


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    keys = tenancy_service.get_tenant_api_keys(db, tenant_id)
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.post("/api-keys", response_model=APIKeyCreatedResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    db_key, raw_key = tenancy_service.create_api_key(db, tenant_id, key_data)
    
    response = APIKeyCreatedResponse.model_validate(db_key)
    response.api_key = raw_key
    return response


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    success = tenancy_service.revoke_api_key(db, key_id, tenant_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key revoked successfully"}


@router.get("/usage/summary", response_model=UsageSummary)
async def get_usage_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    tenant_id = int(current_user["sub"])
    summary = usage_service.get_usage_summary(db, tenant_id, days)
    return UsageSummary(**summary)


@router.get("/usage/dashboard")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = 30
):
    tenant_id = int(current_user["sub"])
    
    summary = usage_service.get_usage_summary(db, tenant_id, days)
    time_series = usage_service.get_usage_over_time(db, tenant_id, days)
    top_models = usage_service.get_top_models(db, tenant_id, days)
    
    return {
        "period": f"Last {days} days",
        "total_requests": summary["total_requests"],
        "total_tokens": summary["total_tokens"],
        "total_cost": summary["total_cost"],
        "avg_latency_ms": summary["avg_latency_ms"],
        "success_rate": summary["success_rate"],
        "top_models": top_models,
        "usage_over_time": time_series
    }


@router.get("/models", response_model=List[ModelInfo])
async def list_all_models(
    current_user: dict = Depends(get_current_user)
):
    models = router_service.get_available_models()
    return [ModelInfo(**m) for m in models]
