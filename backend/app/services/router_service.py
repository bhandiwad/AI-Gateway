import os
import time
import uuid
from typing import Optional, Dict, Any, List, AsyncGenerator
import litellm
from litellm import acompletion, aembedding
import structlog
import asyncio

from backend.app.core.config import settings

logger = structlog.get_logger()


MODEL_COSTS = {
    "gpt-4": {"input": 0.00003, "output": 0.00006},
    "gpt-4-turbo": {"input": 0.00001, "output": 0.00003},
    "gpt-4o": {"input": 0.000005, "output": 0.000015},
    "gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
    "gpt-3.5-turbo": {"input": 0.0000005, "output": 0.0000015},
    "claude-3-opus": {"input": 0.000015, "output": 0.000075},
    "claude-3-sonnet": {"input": 0.000003, "output": 0.000015},
    "claude-3-haiku": {"input": 0.00000025, "output": 0.00000125},
    "claude-3-5-sonnet": {"input": 0.000003, "output": 0.000015},
}


PROVIDER_MODELS = {
    "openai": [
        "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", 
        "gpt-3.5-turbo", "text-embedding-3-small", "text-embedding-3-large"
    ],
    "anthropic": [
        "claude-3-opus-20240229", "claude-3-sonnet-20240229", 
        "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"
    ],
}


class RouterService:
    def __init__(self):
        self.fallback_order = ["openai", "anthropic"]
        litellm.drop_params = True
        litellm.set_verbose = False
    
    def get_provider_for_model(self, model: str) -> str:
        model_lower = model.lower()
        
        if "gpt" in model_lower or "text-embedding" in model_lower or "dall-e" in model_lower:
            return "openai"
        elif "claude" in model_lower:
            return "anthropic"
        else:
            return "openai"
    
    def calculate_cost(
        self, 
        model: str, 
        prompt_tokens: int, 
        completion_tokens: int
    ) -> float:
        model_key = None
        for key in MODEL_COSTS:
            if key in model.lower():
                model_key = key
                break
        
        if model_key:
            costs = MODEL_COSTS[model_key]
            return (prompt_tokens * costs["input"]) + (completion_tokens * costs["output"])
        
        return (prompt_tokens * 0.00001) + (completion_tokens * 0.00002)
    
    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        provider = self.get_provider_for_model(model)
        
        try:
            litellm_messages = []
            for msg in messages:
                litellm_msg = {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                }
                if msg.get("name"):
                    litellm_msg["name"] = msg["name"]
                litellm_messages.append(litellm_msg)
            
            response = await acompletion(
                model=model,
                messages=litellm_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            if stream:
                return {
                    "stream": response,
                    "request_id": request_id,
                    "provider": provider,
                    "model": model,
                    "start_time": start_time
                }
            
            usage = response.usage
            cost = self.calculate_cost(
                model,
                usage.prompt_tokens,
                usage.completion_tokens
            )
            
            return {
                "response": response.model_dump(),
                "request_id": request_id,
                "provider": provider,
                "model": model,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "cost": cost,
                "latency_ms": latency_ms
            }
            
        except Exception as e:
            logger.error("chat_completion_error", model=model, error=str(e))
            raise
    
    async def stream_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        request_id = str(uuid.uuid4())
        provider = self.get_provider_for_model(model)
        
        try:
            litellm_messages = []
            for msg in messages:
                litellm_msg = {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                }
                litellm_messages.append(litellm_msg)
            
            response = await acompletion(
                model=model,
                messages=litellm_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        yield f"data: {chunk.model_dump_json()}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error("stream_error", model=model, error=str(e))
            yield f"data: {{'error': '{str(e)}'}}\n\n"
    
    async def embedding(
        self,
        model: str,
        input_text: Any,
        **kwargs
    ) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        provider = self.get_provider_for_model(model)
        
        try:
            response = await aembedding(
                model=model,
                input=input_text,
                **kwargs
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            usage = response.usage if hasattr(response, 'usage') else {"prompt_tokens": 0, "total_tokens": 0}
            prompt_tokens = usage.get("prompt_tokens", 0) if isinstance(usage, dict) else getattr(usage, 'prompt_tokens', 0)
            
            return {
                "response": response.model_dump(),
                "request_id": request_id,
                "provider": provider,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": 0,
                "total_tokens": prompt_tokens,
                "cost": prompt_tokens * 0.0000001,
                "latency_ms": latency_ms
            }
            
        except Exception as e:
            logger.error("embedding_error", model=model, error=str(e))
            raise
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        models = []
        
        for provider, provider_models in PROVIDER_MODELS.items():
            for model in provider_models:
                costs = MODEL_COSTS.get(model, {"input": 0.00001, "output": 0.00002})
                models.append({
                    "id": model,
                    "name": model,
                    "provider": provider,
                    "context_length": 128000 if "gpt-4" in model or "claude-3" in model else 16000,
                    "input_cost_per_token": costs.get("input", 0.00001),
                    "output_cost_per_token": costs.get("output", 0.00002),
                    "supports_streaming": "embedding" not in model,
                    "supports_functions": "gpt" in model or "claude" in model,
                    "supports_vision": "4o" in model or "claude-3" in model
                })
        
        return models


router_service = RouterService()
