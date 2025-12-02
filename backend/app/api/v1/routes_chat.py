import time
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.core.security import verify_api_key, hash_api_key
from backend.app.core.rate_limit import rate_limiter
from backend.app.services.router_service import router_service
from backend.app.services.guardrails_service import guardrails_service, GuardrailAction
from backend.app.services.tenancy_service import tenancy_service
from backend.app.services.usage_service import usage_service
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
    result = tenancy_service.validate_api_key(db, api_key)
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
    
    rate_key = f"tenant:{tenant.id}"
    rate_limit = api_key.rate_limit_override or tenant.rate_limit
    is_limited, count, remaining = await rate_limiter.is_rate_limited(rate_key, rate_limit)
    
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {rate_limit}/minute"
        )
    
    messages_dict = [msg.model_dump() for msg in request.messages]
    guardrail_result = guardrails_service.validate_request(
        messages_dict,
        tenant.id
    )
    
    if not guardrail_result.passed:
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
    
    try:
        if request.stream:
            async def generate():
                async for chunk in router_service.stream_chat_completion(
                    model=request.model,
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
        
        result = await router_service.chat_completion(
            model=request.model,
            messages=messages_dict,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            stop=request.stop
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
        
        return result["response"]
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        usage_service.log_usage(
            db=db,
            tenant_id=tenant.id,
            api_key_id=api_key.id,
            request_id=request_id,
            endpoint="chat/completions",
            model=request.model,
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
        result = await router_service.embedding(
            model=request.model,
            input_text=request.input
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
