from typing import Optional, List
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.core.security import create_access_token, get_current_user
from backend.app.core.permissions import (
    Permission, get_current_user_with_permissions, RequirePermission,
    get_role_permissions, get_user_from_token
)
from backend.app.db.models.user import UserRole
from backend.app.services.tenancy_service import tenancy_service
from backend.app.services.usage_service import usage_service
from backend.app.services.router_service import router_service
from backend.app.services.sso_service import sso_service
from backend.app.services.user_service import user_service
from backend.app.schemas.tenant import (
    TenantCreate, TenantUpdate, TenantResponse, 
    TenantLogin, TokenResponse
)
from backend.app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyCreatedResponse
from backend.app.schemas.usage import UsageSummary, DashboardStats
from backend.app.schemas.policy import ModelInfo
from backend.app.schemas.sso import (
    SSOConfigCreate, SSOConfigUpdate, SSOConfigResponse,
    SSOLoginInitiate, SSOAuthResponse, OIDCDiscoveryRequest, OIDCDiscoveryResponse
)

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
    
    user = None
    if not tenant:
        user = user_service.get_user_by_email_global(db, credentials.email)
        if user and user.password_hash:
            if user_service.verify_password(credentials.password, user.password_hash):
                tenant = tenancy_service.get_tenant_by_id(db, user.tenant_id)
            else:
                user = None
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token_data = {
        "sub": str(tenant.id), 
        "email": credentials.email,
        "is_admin": tenant.is_admin
    }
    if user:
        token_data["user_id"] = user.id
        token_data["role"] = user.role.value if hasattr(user.role, 'value') else user.role
    
    access_token = create_access_token(data=token_data)
    
    return TokenResponse(
        access_token=access_token,
        tenant=TenantResponse.model_validate(tenant)
    )


@router.get("/auth/me")
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
    
    user = get_user_from_token(current_user, db)
    
    if user:
        user_role = user.role
    elif tenant.is_admin:
        user_role = UserRole.ADMIN
    else:
        user_role = UserRole.MANAGER
    
    permissions = get_role_permissions(user_role)
    
    tenant_data = TenantResponse.model_validate(tenant).model_dump()
    tenant_data["role"] = user_role.value if hasattr(user_role, 'value') else user_role
    tenant_data["permissions"] = [p.value for p in permissions]
    
    if user:
        tenant_data["name"] = user.name
        tenant_data["email"] = user.email
        tenant_data["user_id"] = user.id
    
    return tenant_data


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
    current_user: dict = Depends(RequirePermission(Permission.API_KEYS_VIEW)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    keys = tenancy_service.get_tenant_api_keys(db, tenant_id)
    return [APIKeyResponse.model_validate(k) for k in keys]


@router.post("/api-keys", response_model=APIKeyCreatedResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: dict = Depends(RequirePermission(Permission.API_KEYS_CREATE)),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    db_key, raw_key = tenancy_service.create_api_key(db, tenant_id, key_data)
    
    base_response = APIKeyResponse.model_validate(db_key)
    return APIKeyCreatedResponse(
        **base_response.model_dump(),
        api_key=raw_key
    )


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: dict = Depends(RequirePermission(Permission.API_KEYS_REVOKE)),
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


@router.get("/sso/config", response_model=SSOConfigResponse)
async def get_sso_config(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    config = sso_service.get_sso_config(db, tenant_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSO configuration not found"
        )
    return SSOConfigResponse.model_validate(config)


@router.post("/sso/config", response_model=SSOConfigResponse)
async def create_sso_config(
    config_data: SSOConfigCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    
    existing = sso_service.get_sso_config(db, tenant_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSO configuration already exists. Use PUT to update."
        )
    
    config = sso_service.create_sso_config(db, tenant_id, config_data.model_dump())
    return SSOConfigResponse.model_validate(config)


@router.put("/sso/config", response_model=SSOConfigResponse)
async def update_sso_config(
    config_data: SSOConfigUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    
    config = sso_service.update_sso_config(
        db, tenant_id, config_data.model_dump(exclude_unset=True)
    )
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSO configuration not found"
        )
    
    return SSOConfigResponse.model_validate(config)


@router.delete("/sso/config")
async def delete_sso_config(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tenant_id = int(current_user["sub"])
    
    success = sso_service.delete_sso_config(db, tenant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSO configuration not found"
        )
    
    return {"message": "SSO configuration deleted successfully"}


@router.post("/sso/discover", response_model=OIDCDiscoveryResponse)
async def discover_oidc_provider(
    request: OIDCDiscoveryRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        config = await sso_service.discover_oidc_config(request.issuer_url)
        return OIDCDiscoveryResponse(**config)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OIDC discovery failed: {str(e)}"
        )


@router.get("/auth/sso/providers")
async def list_sso_providers(db: Session = Depends(get_db)):
    providers = sso_service.list_enabled_providers(db)
    return {"providers": providers}


@router.post("/auth/sso/initiate")
async def initiate_sso_login(
    request: SSOLoginInitiate,
    db: Session = Depends(get_db)
):
    config = sso_service.get_sso_config_by_provider(db, request.provider_name)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SSO provider '{request.provider_name}' not found or not enabled"
        )
    
    auth_url, state = await sso_service.generate_authorization_url(
        config, request.redirect_uri
    )
    
    return {
        "authorization_url": auth_url,
        "state": state
    }


@router.get("/auth/sso/callback")
async def sso_callback(
    code: str = Query(...),
    state: str = Query(...),
    provider_name: str = Query(...),
    db: Session = Depends(get_db)
):
    config = sso_service.get_sso_config_by_provider(db, provider_name)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SSO provider not found"
        )
    
    try:
        auth_result = await sso_service.authenticate_sso_user(
            db, config, code, state, provider_name
        )
        return auth_result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
