import time
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.core.config import settings
from backend.app.core.security import verify_api_key
from backend.app.core.rate_limit import rate_limiter
from backend.app.services.router_service import router_service
from backend.app.services.guardrails_service import guardrails_service, GuardrailAction
from backend.app.services.guardrails_service_async import async_guardrails_service
from backend.app.services.guardrail_resolver import guardrail_resolver
from backend.app.services.tenancy_service import tenancy_service
from backend.app.services.usage_service import usage_service
from backend.app.services.budget_enforcement_service import BudgetEnforcementService
from backend.app.core.api_key_cache import api_key_cache
from backend.app.core.security import hash_api_key
from backend.app.schemas.chat import (
    ChatCompletionRequest, ChatCompletionResponse,
    EmbeddingRequest, EmbeddingResponse,
    ImageGenerationRequest, ImageGenerationResponse
)

router = APIRouter()


async def get_tenant_from_api_key(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    # OPTIMIZATION: Use cached API key validation
    api_key_hash = hash_api_key(api_key)
    result = await api_key_cache.get_tenant_and_key(db, api_key_hash)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )
    return result


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    tenant_info: tuple = Depends(get_tenant_from_api_key),
    db: Session = Depends(get_db)
):
    tenant, api_key = tenant_info
    request_id = str(uuid.uuid4())
    start_time = time.time()
    cache_hit = False
    content_category = None
    routing_decision = None
    request_path = "/v1/chat/completions"
    
    rate_key = f"tenant:{tenant.id}"
    rate_limit = api_key.rate_limit_override or tenant.rate_limit
    is_limited, count, remaining = await rate_limiter.is_rate_limited(rate_key, rate_limit)
    
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {rate_limit}/minute"
        )
    
    budget_service = BudgetEnforcementService(db)
    budget_check = budget_service.check_budget(
        tenant_id=tenant.id,
        model=request.model or "unknown",
        estimated_cost=0.01,
        api_key_id=api_key.id,
        user_id=api_key.owner_user_id,
        team_id=api_key.team_id,
        department_id=api_key.department_id,
        route_id=None
    )
    
    if not budget_check.allowed:
        usage_service.log_usage(
            db=db,
            tenant_id=tenant.id,
            api_key_id=api_key.id,
            request_id=request_id,
            endpoint="chat/completions",
            model=request.model or "unknown",
            provider="budget_blocked",
            status="blocked",
            error_message=budget_check.message
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=budget_check.message
        )
    
    allowed_models = guardrail_resolver.resolve_allowed_models(
        db=db,
        request_path=request_path,
        api_key=api_key,
        tenant=tenant
    )
    
    if allowed_models and request.model and request.model not in allowed_models:
        usage_service.log_usage(
            db=db,
            tenant_id=tenant.id,
            api_key_id=api_key.id,
            request_id=request_id,
            endpoint="chat/completions",
            model=request.model,
            provider="blocked",
            status="blocked",
            error_message=f"Model '{request.model}' is not allowed for this API key/route"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Model '{request.model}' is not allowed. Allowed models: {', '.join(allowed_models)}"
        )
    
    messages_dict = [msg.model_dump() for msg in request.messages]
    
    context = {
        "department_id": api_key.department_id,
        "team_id": api_key.team_id,
        "api_key_tags": api_key.tags or [],
        "environment": api_key.environment
    }
    
    guardrail_profile = guardrail_resolver.resolve_profile(
        db=db,
        request_path=request_path,
        api_key=api_key,
        tenant=tenant,
        context=context
    )
    
    if guardrail_profile:
        from backend.app.services.profile_guardrails_service import apply_profile_guardrails
        profile_result = apply_profile_guardrails(
            profile=guardrail_profile,
            messages=messages_dict,
            stage="request",
            tenant_id=tenant.id
        )
        if not profile_result.passed:
            usage_service.log_usage(
                db=db,
                tenant_id=tenant.id,
                api_key_id=api_key.id,
                request_id=request_id,
                endpoint="chat/completions",
                model=request.model,
                provider="blocked",
                status="blocked",
                error_message=profile_result.message,
                guardrail_triggered=profile_result.triggered_processor,
                guardrail_action=profile_result.action
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=profile_result.message
            )
        messages_dict = profile_result.processed_messages or messages_dict
    else:
        guardrail_result = guardrails_service.validate_request(
            messages_dict,
            tenant.id
        )
        
        if not guardrail_result.passed:
            if settings.ENABLE_TELEMETRY:
                from backend.app.telemetry import record_llm_metrics
                record_llm_metrics(
                    model=request.model,
                    provider="blocked",
                    tenant_id=tenant.id,
                    status="blocked",
                    guardrail_triggered=guardrail_result.triggered_rule
                )
            
            usage_service.log_usage(
                db=db,
                tenant_id=tenant.id,
                api_key_id=api_key.id,
                request_id=request_id,
                endpoint="chat/completions",
                model=request.model,
                provider="blocked",
                status="blocked",
                error_message=guardrail_result.message,
                guardrail_triggered=guardrail_result.triggered_rule,
                guardrail_action=guardrail_result.action.value
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=guardrail_result.message
            )
    
    model_to_use = request.model
    
    if settings.ENABLE_CONTENT_ROUTING and not request.model:
        from backend.app.services.content_routing_service import content_routing_service
        model_to_use, content_category, routing_decision = content_routing_service.get_recommended_model(
            messages=messages_dict,
            requested_model=request.model,
            tenant_id=tenant.id
        )
    
    if settings.ENABLE_SEMANTIC_CACHE and not request.stream:
        from backend.app.services.semantic_cache_service import semantic_cache
        cached_response = await semantic_cache.get_cached_response(
            messages=messages_dict,
            model=model_to_use,
            tenant_id=tenant.id
        )
        
        if cached_response:
            cache_hit = True
            latency_ms = int((time.time() - start_time) * 1000)
            
            if settings.ENABLE_TELEMETRY:
                from backend.app.telemetry import record_llm_metrics
                record_llm_metrics(
                    model=model_to_use,
                    provider="cache",
                    tenant_id=tenant.id,
                    latency_ms=latency_ms,
                    cache_hit=True,
                    status="success"
                )
            
            usage_service.log_usage(
                db=db,
                tenant_id=tenant.id,
                api_key_id=api_key.id,
                request_id=request_id,
                endpoint="chat/completions",
                model=model_to_use,
                provider="cache",
                prompt_tokens=0,
                completion_tokens=0,
                cost=0.0,
                latency_ms=latency_ms,
                status="cache_hit"
            )
            
            response = cached_response.copy()
            response["cache_hit"] = True
            response["similarity"] = cached_response.get("similarity", 1.0)
            return response
    
    try:
        if request.stream:
            if settings.ENABLE_STREAM_INSPECTION:
                from backend.app.services.stream_inspection_service import stream_inspection_service
                
                base_stream = router_service.stream_chat_completion(
                    model=model_to_use,
                    messages=messages_dict,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
                
                def on_violation(result):
                    usage_service.log_usage(
                        db=db,
                        tenant_id=tenant.id,
                        api_key_id=api_key.id,
                        request_id=request_id,
                        endpoint="chat/completions",
                        model=model_to_use,
                        provider=router_service.get_provider_for_model(model_to_use),
                        status="stream_blocked",
                        error_message=result.message,
                        guardrail_triggered=result.triggered_rule,
                        guardrail_action="block"
                    )
                
                async def inspected_generate():
                    async for chunk in stream_inspection_service.create_inspected_stream(
                        stream=base_stream,
                        request_id=request_id,
                        tenant_id=tenant.id,
                        model=model_to_use,
                        on_violation=on_violation
                    ):
                        yield chunk
                
                return StreamingResponse(
                    inspected_generate(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Request-ID": request_id,
                        "X-Stream-Inspection": "enabled"
                    }
                )
            else:
                async def generate():
                    async for chunk in router_service.stream_chat_completion(
                        model=model_to_use,
                        messages=messages_dict,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens
                    ):
                        yield chunk
                
                return StreamingResponse(
                    generate(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Request-ID": request_id
                    }
                )
        
        if settings.ENABLE_TELEMETRY:
            from backend.app.telemetry import create_span
            from opentelemetry.trace import SpanKind
            
            with create_span("llm.chat_completion", SpanKind.CLIENT, {
                "llm.model": model_to_use,
                "llm.temperature": request.temperature,
                "llm.max_tokens": request.max_tokens,
                "tenant.id": tenant.id
            }):
                result = await router_service.chat_completion(
                    model=model_to_use,
                    messages=messages_dict,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    top_p=request.top_p,
                    presence_penalty=request.presence_penalty,
                    frequency_penalty=request.frequency_penalty,
                    stop=request.stop
                )
        else:
            result = await router_service.chat_completion(
                model=model_to_use,
                messages=messages_dict,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                presence_penalty=request.presence_penalty,
                frequency_penalty=request.frequency_penalty,
                stop=request.stop
            )
        
        if settings.ENABLE_SEMANTIC_CACHE:
            from backend.app.services.semantic_cache_service import semantic_cache
            await semantic_cache.cache_response(
                messages=messages_dict,
                model=model_to_use,
                tenant_id=tenant.id,
                response=result["response"]
            )
        
        if settings.ENABLE_TELEMETRY:
            from backend.app.telemetry import record_llm_metrics
            record_llm_metrics(
                model=result["model"],
                provider=result["provider"],
                tenant_id=tenant.id,
                prompt_tokens=result["prompt_tokens"],
                completion_tokens=result["completion_tokens"],
                latency_ms=result["latency_ms"],
                cost=result["cost"],
                cache_hit=False,
                status="success"
            )
        
        usage_service.log_usage(
            db=db,
            tenant_id=tenant.id,
            api_key_id=api_key.id,
            request_id=result["request_id"],
            endpoint="chat/completions",
            model=result["model"],
            provider=result["provider"],
            prompt_tokens=result["prompt_tokens"],
            completion_tokens=result["completion_tokens"],
            cost=result["cost"],
            latency_ms=result["latency_ms"],
            status="success"
        )
        
        tenancy_service.update_tenant_spend(db, tenant.id, result["cost"])
        
        response = result["response"]
        
        if routing_decision:
            response["_routing"] = routing_decision
        
        return response
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        
        if settings.ENABLE_TELEMETRY:
            from backend.app.telemetry import record_llm_metrics
            record_llm_metrics(
                model=model_to_use,
                provider="error",
                tenant_id=tenant.id,
                latency_ms=latency_ms,
                status="error"
            )
        
        usage_service.log_usage(
            db=db,
            tenant_id=tenant.id,
            api_key_id=api_key.id,
            request_id=request_id,
            endpoint="chat/completions",
            model=model_to_use,
            provider="error",
            latency_ms=latency_ms,
            status="error",
            error_message=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@router.post("/embeddings")
async def create_embeddings(
    request: EmbeddingRequest,
    tenant_info: tuple = Depends(get_tenant_from_api_key),
    db: Session = Depends(get_db)
):
    tenant, api_key = tenant_info
    request_id = str(uuid.uuid4())
    
    rate_key = f"tenant:{tenant.id}"
    is_limited, _, _ = await rate_limiter.is_rate_limited(rate_key)
    
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    try:
        if settings.ENABLE_TELEMETRY:
            from backend.app.telemetry import create_span
            from opentelemetry.trace import SpanKind
            
            with create_span("llm.embedding", SpanKind.CLIENT, {
                "llm.model": request.model,
                "tenant.id": tenant.id
            }):
                result = await router_service.embedding(
                    model=request.model,
                    input_text=request.input
                )
        else:
            result = await router_service.embedding(
                model=request.model,
                input_text=request.input
            )
        
        if settings.ENABLE_TELEMETRY:
            from backend.app.telemetry import record_llm_metrics
            record_llm_metrics(
                model=result["model"],
                provider=result["provider"],
                tenant_id=tenant.id,
                prompt_tokens=result["prompt_tokens"],
                latency_ms=result["latency_ms"],
                cost=result["cost"],
                status="success"
            )
        
        usage_service.log_usage(
            db=db,
            tenant_id=tenant.id,
            api_key_id=api_key.id,
            request_id=result["request_id"],
            endpoint="embeddings",
            model=result["model"],
            provider=result["provider"],
            prompt_tokens=result["prompt_tokens"],
            cost=result["cost"],
            latency_ms=result["latency_ms"],
            status="success"
        )
        
        return result["response"]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )


@router.get("/models")
async def list_models(
    tenant_info: tuple = Depends(get_tenant_from_api_key)
):
    tenant, api_key = tenant_info
    
    all_models = router_service.get_available_models()
    
    allowed_models = api_key.allowed_models_override or tenant.allowed_models
    if allowed_models:
        all_models = [m for m in all_models if m["id"] in allowed_models]
    
    return {
        "object": "list",
        "data": all_models
    }


@router.get("/cache/stats")
async def get_cache_stats(
    tenant_info: tuple = Depends(get_tenant_from_api_key)
):
    if not settings.ENABLE_SEMANTIC_CACHE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semantic cache is not enabled"
        )
    
    from backend.app.services.semantic_cache_service import semantic_cache
    return semantic_cache.get_stats()


@router.delete("/cache")
async def clear_tenant_cache(
    tenant_info: tuple = Depends(get_tenant_from_api_key)
):
    if not settings.ENABLE_SEMANTIC_CACHE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semantic cache is not enabled"
        )
    
    tenant, _ = tenant_info
    from backend.app.services.semantic_cache_service import semantic_cache
    await semantic_cache.invalidate_tenant_cache(tenant.id)
    
    return {"message": "Cache cleared successfully"}


@router.get("/routing/config")
async def get_routing_config(
    tenant_info: tuple = Depends(get_tenant_from_api_key)
):
    if not settings.ENABLE_CONTENT_ROUTING:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content routing is not enabled"
        )
    
    tenant, _ = tenant_info
    from backend.app.services.content_routing_service import content_routing_service
    return content_routing_service.get_tenant_routing_config(tenant.id)
