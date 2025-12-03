from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from backend.app.db.session import get_db
from backend.app.core.security import get_current_tenant
from backend.app.services import provider_config_service
from backend.app.core.permissions import require_permission, Permission
from backend.app.db.models import Tenant


router = APIRouter(prefix="/providers", tags=["Provider Configuration"])


class ServiceTypeResponse(BaseModel):
    id: str
    name: str
    description: str
    requires_api_key: bool


class ProviderModelInput(BaseModel):
    model_id: str
    display_name: Optional[str] = None
    context_length: Optional[int] = None
    input_cost_per_1k: Optional[float] = None
    output_cost_per_1k: Optional[float] = None
    capabilities: List[str] = Field(default_factory=list)


class ProviderCreate(BaseModel):
    name: str
    service_type: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    api_key_secret_name: Optional[str] = None
    timeout_seconds: int = 120
    max_retries: int = 3
    traffic_leaves_enterprise: bool = True
    models: List[str] = Field(default_factory=list)
    rate_limit_rpm: Optional[int] = None
    rate_limit_tpm: Optional[int] = None
    priority: int = 0
    config: Dict[str, Any] = Field(default_factory=dict)


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    service_type: Optional[str] = None
    endpoint_url: Optional[str] = None
    api_key_secret_name: Optional[str] = None
    is_active: Optional[bool] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    traffic_leaves_enterprise: Optional[bool] = None
    models: Optional[List[str]] = None
    rate_limit_rpm: Optional[int] = None
    rate_limit_tpm: Optional[int] = None
    priority: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class ProviderResponse(BaseModel):
    id: int
    tenant_id: Optional[int]
    name: str
    display_name: Optional[str]
    description: Optional[str]
    service_type: str
    endpoint_url: Optional[str]
    api_key_secret_name: Optional[str]
    is_active: bool
    priority: int
    timeout_seconds: int
    max_retries: int
    traffic_leaves_enterprise: bool
    models: List[str]
    rate_limit_rpm: Optional[int]
    rate_limit_tpm: Optional[int]
    config: Dict[str, Any]
    
    class Config:
        from_attributes = True


class APIRouteCreate(BaseModel):
    path: str
    description: Optional[str] = None
    policy_id: Optional[int] = None
    default_provider_id: Optional[int] = None
    default_model: Optional[str] = None
    allowed_methods: List[str] = Field(default_factory=lambda: ["POST"])
    request_size_limit_kb: int = 10240
    timeout_seconds: int = 120
    rate_limit_rpm: Optional[int] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class APIRouteUpdate(BaseModel):
    path: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    policy_id: Optional[int] = None
    default_provider_id: Optional[int] = None
    default_model: Optional[str] = None
    allowed_methods: Optional[List[str]] = None
    request_size_limit_kb: Optional[int] = None
    timeout_seconds: Optional[int] = None
    rate_limit_rpm: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class APIRouteResponse(BaseModel):
    id: int
    tenant_id: Optional[int]
    path: str
    description: Optional[str]
    is_active: bool
    policy_id: Optional[int]
    default_provider_id: Optional[int]
    default_model: Optional[str]
    allowed_methods: List[str]
    request_size_limit_kb: int
    timeout_seconds: int
    rate_limit_rpm: Optional[int]
    config: Dict[str, Any]
    
    class Config:
        from_attributes = True


class RoutingPolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    selectors: Dict[str, Any] = Field(default_factory=dict)
    profile_id: Optional[int] = None
    allowed_providers: List[str] = Field(default_factory=list)
    allowed_models: List[str] = Field(default_factory=list)
    priority: int = 0
    config: Dict[str, Any] = Field(default_factory=dict)


class RoutingPolicyResponse(BaseModel):
    id: int
    tenant_id: Optional[int]
    name: str
    description: Optional[str]
    is_active: bool
    priority: int
    selectors: Dict[str, Any]
    profile_id: Optional[int]
    allowed_providers: List[str]
    allowed_models: List[str]
    config: Dict[str, Any]
    
    class Config:
        from_attributes = True


class GuardrailProfileCreate(BaseModel):
    name: str
    description: Optional[str] = None
    request_processors: List[Dict[str, Any]] = Field(default_factory=list)
    response_processors: List[Dict[str, Any]] = Field(default_factory=list)
    logging_level: str = "info"
    config: Dict[str, Any] = Field(default_factory=dict)


class GuardrailProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    request_processors: Optional[List[Dict[str, Any]]] = None
    response_processors: Optional[List[Dict[str, Any]]] = None
    logging_level: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class GuardrailProfileResponse(BaseModel):
    id: int
    tenant_id: Optional[int]
    name: str
    description: Optional[str]
    is_active: bool
    request_processors: List[Dict[str, Any]]
    response_processors: List[Dict[str, Any]]
    logging_level: str
    config: Dict[str, Any]
    
    class Config:
        from_attributes = True


class ProcessorDefinitionResponse(BaseModel):
    id: int
    name: str
    display_name: Optional[str]
    description: Optional[str]
    processor_type: str
    stage: str
    is_active: bool
    is_builtin: bool
    default_config: Dict[str, Any]
    supported_actions: List[str]
    
    class Config:
        from_attributes = True


@router.get("/service-types", response_model=List[ServiceTypeResponse])
async def get_service_types():
    return provider_config_service.get_service_types()


@router.get("", response_model=List[ProviderResponse])
async def list_providers(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_VIEW)
):
    providers = provider_config_service.list_providers(db, tenant.id, include_global=True)
    return providers


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_VIEW)
):
    provider = provider_config_service.get_provider(db, provider_id, tenant.id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.post("", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: ProviderCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_EDIT)
):
    provider = provider_config_service.create_provider(
        db,
        tenant_id=tenant.id,
        name=data.name,
        service_type=data.service_type,
        display_name=data.display_name,
        description=data.description,
        endpoint_url=data.endpoint_url,
        api_key_secret_name=data.api_key_secret_name,
        timeout_seconds=data.timeout_seconds,
        max_retries=data.max_retries,
        traffic_leaves_enterprise=data.traffic_leaves_enterprise,
        models=data.models,
        rate_limit_rpm=data.rate_limit_rpm,
        rate_limit_tpm=data.rate_limit_tpm,
        priority=data.priority,
        config=data.config
    )
    return provider


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: int,
    data: ProviderUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_EDIT)
):
    provider = provider_config_service.update_provider(
        db, provider_id, tenant.id,
        **data.model_dump(exclude_unset=True)
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_EDIT)
):
    success = provider_config_service.delete_provider(db, provider_id, tenant.id)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")


@router.get("/routes/list", response_model=List[APIRouteResponse])
async def list_api_routes(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_VIEW)
):
    routes = provider_config_service.list_api_routes(db, tenant.id)
    return routes


@router.post("/routes", response_model=APIRouteResponse, status_code=status.HTTP_201_CREATED)
async def create_api_route(
    data: APIRouteCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_EDIT)
):
    route = provider_config_service.create_api_route(
        db,
        path=data.path,
        tenant_id=tenant.id,
        description=data.description,
        policy_id=data.policy_id,
        default_provider_id=data.default_provider_id,
        default_model=data.default_model,
        allowed_methods=data.allowed_methods,
        request_size_limit_kb=data.request_size_limit_kb,
        timeout_seconds=data.timeout_seconds,
        rate_limit_rpm=data.rate_limit_rpm,
        config=data.config
    )
    return route


@router.put("/routes/{route_id}", response_model=APIRouteResponse)
async def update_api_route(
    route_id: int,
    data: APIRouteUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_EDIT)
):
    route = provider_config_service.update_api_route(
        db, route_id, tenant.id,
        **data.model_dump(exclude_unset=True)
    )
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


@router.delete("/routes/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_route(
    route_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_EDIT)
):
    success = provider_config_service.delete_api_route(db, route_id, tenant.id)
    if not success:
        raise HTTPException(status_code=404, detail="Route not found")


@router.get("/policies/list", response_model=List[RoutingPolicyResponse])
async def list_routing_policies(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_VIEW)
):
    policies = provider_config_service.list_routing_policies(db, tenant.id)
    return policies


@router.post("/policies", response_model=RoutingPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_routing_policy(
    data: RoutingPolicyCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.ROUTER_EDIT)
):
    policy = provider_config_service.create_routing_policy(
        db,
        name=data.name,
        tenant_id=tenant.id,
        description=data.description,
        selectors=data.selectors,
        profile_id=data.profile_id,
        allowed_providers=data.allowed_providers,
        allowed_models=data.allowed_models,
        priority=data.priority,
        config=data.config
    )
    return policy


@router.get("/profiles/list", response_model=List[GuardrailProfileResponse])
async def list_guardrail_profiles(
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.GUARDRAILS_VIEW)
):
    profiles = provider_config_service.list_guardrail_profiles(db, tenant.id)
    return profiles


@router.post("/profiles", response_model=GuardrailProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_guardrail_profile(
    data: GuardrailProfileCreate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.GUARDRAILS_EDIT)
):
    profile = provider_config_service.create_guardrail_profile(
        db,
        name=data.name,
        tenant_id=tenant.id,
        description=data.description,
        request_processors=data.request_processors,
        response_processors=data.response_processors,
        logging_level=data.logging_level,
        config=data.config
    )
    return profile


@router.put("/profiles/{profile_id}", response_model=GuardrailProfileResponse)
async def update_guardrail_profile(
    profile_id: int,
    data: GuardrailProfileUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.GUARDRAILS_EDIT)
):
    profile = provider_config_service.update_guardrail_profile(
        db,
        profile_id=profile_id,
        tenant_id=tenant.id,
        name=data.name,
        description=data.description,
        request_processors=data.request_processors,
        response_processors=data.response_processors,
        logging_level=data.logging_level,
        config=data.config,
        is_enabled=data.is_enabled
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Guardrail profile not found")
    return profile


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guardrail_profile(
    profile_id: int,
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db),
    _auth: dict = require_permission(Permission.GUARDRAILS_EDIT)
):
    deleted = provider_config_service.delete_guardrail_profile(db, profile_id, tenant.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Guardrail profile not found")
    return None


@router.get("/processors/definitions", response_model=List[ProcessorDefinitionResponse])
async def list_processor_definitions(
    db: Session = Depends(get_db)
):
    provider_config_service.seed_processor_definitions(db)
    return provider_config_service.list_processor_definitions(db)
