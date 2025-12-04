from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog

from backend.app.core.security import get_current_user
from backend.app.core.permissions import require_permission
from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.db.models.external_guardrail_provider import ExternalGuardrailProvider
from backend.app.schemas.external_guardrail import (
    ExternalGuardrailProviderCreate,
    ExternalGuardrailProviderUpdate,
    ExternalGuardrailProviderResponse,
    GuardrailCheckRequest,
    GuardrailCheckResponse,
    ProviderHealthResponse
)
from backend.app.services.guardrail_provider_manager import guardrail_provider_manager
from backend.app.services.guardrail_providers import GuardrailProviderConfig

logger = structlog.get_logger()
router = APIRouter()


# ==================== PROVIDER MANAGEMENT ====================

@router.post("/providers", response_model=ExternalGuardrailProviderResponse)
@require_permission("settings:edit")
async def create_external_provider(
    provider_data: ExternalGuardrailProviderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new external guardrail provider."""
    # Create provider in database
    provider = ExternalGuardrailProvider(
        tenant_id=current_user.tenant_id if not provider_data.is_global else None,
        name=provider_data.name,
        provider_type=provider_data.provider_type,
        description=provider_data.description,
        api_key_encrypted=provider_data.api_key,  # TODO: Encrypt this
        api_endpoint=provider_data.api_endpoint,
        region=provider_data.region,
        timeout_seconds=provider_data.timeout_seconds,
        retry_attempts=provider_data.retry_attempts,
        priority=provider_data.priority,
        thresholds=provider_data.thresholds,
        custom_config=provider_data.custom_config,
        is_global=provider_data.is_global,
        is_enabled=True
    )
    
    db.add(provider)
    db.commit()
    db.refresh(provider)
    
    # Register with provider manager
    config = GuardrailProviderConfig(
        enabled=True,
        api_key=provider_data.api_key,
        api_endpoint=provider_data.api_endpoint,
        region=provider_data.region,
        timeout_seconds=provider_data.timeout_seconds,
        retry_attempts=provider_data.retry_attempts,
        thresholds=provider_data.thresholds,
        custom_config=provider_data.custom_config
    )
    
    success = guardrail_provider_manager.register_provider(
        provider_name=f"{provider.id}_{provider.name}",
        provider_type=provider.provider_type,
        config=config
    )
    
    if success:
        # Update capabilities
        registered_provider = guardrail_provider_manager.providers.get(f"{provider.id}_{provider.name}")
        if registered_provider:
            provider.capabilities = [c.value for c in registered_provider.get_capabilities()]
            db.commit()
            db.refresh(provider)
    
    logger.info(
        "external_guardrail_provider_created",
        provider_id=provider.id,
        provider_type=provider.provider_type,
        tenant_id=current_user.tenant_id
    )
    
    return provider


@router.get("/providers", response_model=List[ExternalGuardrailProviderResponse])
@require_permission("guardrails:view")
async def list_external_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all external guardrail providers."""
    providers = db.query(ExternalGuardrailProvider).filter(
        (ExternalGuardrailProvider.tenant_id == current_user.tenant_id) |
        (ExternalGuardrailProvider.is_global == True)
    ).all()
    
    return providers


@router.get("/providers/{provider_id}", response_model=ExternalGuardrailProviderResponse)
@require_permission("guardrails:view")
async def get_external_provider(
    provider_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get external guardrail provider by ID."""
    provider = db.query(ExternalGuardrailProvider).filter(
        ExternalGuardrailProvider.id == provider_id,
        (ExternalGuardrailProvider.tenant_id == current_user.tenant_id) |
        (ExternalGuardrailProvider.is_global == True)
    ).first()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    
    return provider


@router.put("/providers/{provider_id}", response_model=ExternalGuardrailProviderResponse)
@require_permission("settings:edit")
async def update_external_provider(
    provider_id: int,
    provider_update: ExternalGuardrailProviderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update external guardrail provider."""
    provider = db.query(ExternalGuardrailProvider).filter(
        ExternalGuardrailProvider.id == provider_id,
        ExternalGuardrailProvider.tenant_id == current_user.tenant_id
    ).first()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    
    update_dict = provider_update.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        if key == "api_key":
            setattr(provider, "api_key_encrypted", value)  # TODO: Encrypt
        else:
            setattr(provider, key, value)
    
    db.commit()
    db.refresh(provider)
    
    logger.info(
        "external_guardrail_provider_updated",
        provider_id=provider_id,
        tenant_id=current_user.tenant_id
    )
    
    return provider


@router.delete("/providers/{provider_id}")
@require_permission("settings:edit")
async def delete_external_provider(
    provider_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete external guardrail provider."""
    provider = db.query(ExternalGuardrailProvider).filter(
        ExternalGuardrailProvider.id == provider_id,
        ExternalGuardrailProvider.tenant_id == current_user.tenant_id
    ).first()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    
    # Unregister from manager
    guardrail_provider_manager.unregister_provider(f"{provider.id}_{provider.name}")
    
    db.delete(provider)
    db.commit()
    
    logger.info(
        "external_guardrail_provider_deleted",
        provider_id=provider_id,
        tenant_id=current_user.tenant_id
    )
    
    return {"message": "Provider deleted successfully"}


# ==================== PROVIDER TESTING ====================

@router.post("/providers/{provider_id}/test", response_model=GuardrailCheckResponse)
@require_permission("guardrails:test")
async def test_external_provider(
    provider_id: int,
    request: GuardrailCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test an external guardrail provider with sample text."""
    provider = db.query(ExternalGuardrailProvider).filter(
        ExternalGuardrailProvider.id == provider_id,
        (ExternalGuardrailProvider.tenant_id == current_user.tenant_id) |
        (ExternalGuardrailProvider.is_global == True)
    ).first()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )
    
    provider_name = f"{provider.id}_{provider.name}"
    
    if request.stage == "input":
        result = await guardrail_provider_manager.check_input(
            text=request.text,
            context=request.context,
            providers=[provider_name]
        )
    else:
        result = await guardrail_provider_manager.check_output(
            text=request.text,
            context=request.context,
            providers=[provider_name]
        )
    
    return GuardrailCheckResponse(
        provider=result.provider,
        passed=result.passed,
        violations=[v.model_dump() for v in result.violations],
        recommended_action=result.recommended_action.value,
        processing_time_ms=result.processing_time_ms,
        metadata=result.metadata
    )


@router.post("/check", response_model=GuardrailCheckResponse)
@require_permission("guardrails:test")
async def check_with_providers(
    request: GuardrailCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check text using multiple external providers."""
    if request.stage == "input":
        result = await guardrail_provider_manager.check_input(
            text=request.text,
            context=request.context,
            providers=request.providers
        )
    else:
        result = await guardrail_provider_manager.check_output(
            text=request.text,
            context=request.context,
            providers=request.providers
        )
    
    return GuardrailCheckResponse(
        provider=result.provider,
        passed=result.passed,
        violations=[v.model_dump() for v in result.violations],
        recommended_action=result.recommended_action.value,
        processing_time_ms=result.processing_time_ms,
        metadata=result.metadata
    )


# ==================== HEALTH CHECK ====================

@router.get("/providers/health/all", response_model=List[ProviderHealthResponse])
@require_permission("guardrails:view")
async def health_check_all_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check health of all registered external providers."""
    health_results = await guardrail_provider_manager.health_check_all()
    
    providers = db.query(ExternalGuardrailProvider).filter(
        (ExternalGuardrailProvider.tenant_id == current_user.tenant_id) |
        (ExternalGuardrailProvider.is_global == True)
    ).all()
    
    response = []
    for provider in providers:
        provider_name = f"{provider.id}_{provider.name}"
        is_healthy = health_results.get(provider_name, False)
        
        # Update health status
        provider.is_healthy = is_healthy
        provider.last_health_check = db.func.now()
        
        response.append(ProviderHealthResponse(
            provider_name=provider.name,
            is_healthy=is_healthy,
            last_check=provider.last_health_check,
            capabilities=provider.capabilities
        ))
    
    db.commit()
    
    return response


# ==================== PROVIDER INFO ====================

@router.get("/providers/info/all")
@require_permission("guardrails:view")
async def get_all_provider_info(
    current_user: User = Depends(get_current_user)
):
    """Get information about all registered providers in the manager."""
    return guardrail_provider_manager.get_provider_info()
