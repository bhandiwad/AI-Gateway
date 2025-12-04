import os
import time
import uuid
from typing import Optional, Dict, Any, List, AsyncGenerator
import litellm
from litellm import acompletion, aembedding
import structlog
import asyncio

from backend.app.core.config import settings
from backend.app.services.load_balancer import load_balancer, LoadBalancingStrategy
from backend.app.services.circuit_breaker import circuit_breaker_manager, CircuitBreakerOpenError, CircuitBreakerConfig
from backend.app.services.request_transformer import request_transformer, response_transformer

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
    "mock": [
        "mock-gpt-4", "mock-claude"
    ],
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
        self._initialize_load_balancing()
        self._initialize_circuit_breakers()
    
    def _initialize_load_balancing(self):
        """Initialize load balancer with provider pools"""
        # Register provider pools for models with multiple endpoints
        # Example: Multiple OpenAI endpoints for load balancing
        load_balancer.register_provider_pool(
            "gpt-4",
            [{"name": "openai", "weight": 1}],
            LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN
        )
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers with default config"""
        # Circuit breakers are created on-demand, but we can set default config
        default_config = CircuitBreakerConfig(
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=30,
            window_seconds=60
        )
        circuit_breaker_manager.set_default_config(default_config)
    
    def get_provider_for_model(self, model: str) -> str:
        model_lower = model.lower()
        
        if "mock" in model_lower:
            return "mock"
        elif "gpt" in model_lower or "text-embedding" in model_lower or "dall-e" in model_lower:
            return "openai"
        elif "claude" in model_lower:
            return "anthropic"
        else:
            return "openai"
    
    def _generate_mock_response(self, messages: List[Dict[str, Any]], model: str) -> Dict[str, Any]:
        last_message = messages[-1].get("content", "") if messages else "Hello"
        mock_content = f"This is a mock response from {model}. You said: '{last_message[:100]}...'" if len(last_message) > 100 else f"This is a mock response from {model}. You said: '{last_message}'"
        
        return {
            "id": f"mock-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": mock_content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(str(messages)) // 4,
                "completion_tokens": len(mock_content) // 4,
                "total_tokens": (len(str(messages)) + len(mock_content)) // 4
            }
        }
    
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
        tenant_id: Optional[int] = None,
        api_key_id: Optional[int] = None,
        user_id: Optional[int] = None,
        route_path: str = "/chat/completions",
        **kwargs
    ) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Apply request transformations
        request_data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        context = {
            "tenant_id": tenant_id,
            "api_key_id": api_key_id,
            "user_id": user_id
        }
        request_data = request_transformer.transform_request(route_path, request_data, context)
        
        # Extract transformed values
        model = request_data.get("model", model)
        messages = request_data.get("messages", messages)
        temperature = request_data.get("temperature", temperature)
        max_tokens = request_data.get("max_tokens", max_tokens)
        
        # Select provider with load balancing
        provider = self._select_provider_with_load_balancing(model)
        
        # Try with circuit breaker protection
        tried_providers = []
        last_error = None
        
        for attempt_provider in [provider] + self.fallback_order:
            if attempt_provider in tried_providers:
                continue
            tried_providers.append(attempt_provider)
            
            try:
                # Check circuit breaker
                breaker = circuit_breaker_manager.get_breaker(attempt_provider)
                if not breaker.can_execute():
                    logger.warning(
                        "circuit_breaker_open",
                        provider=attempt_provider,
                        state=breaker.state
                    )
                    continue
                
                # Mark load balancer request start
                load_balancer.mark_request_start(model, attempt_provider)
                
                result = await self._execute_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                    provider=attempt_provider,
                    request_id=request_id,
                    start_time=start_time,
                    **kwargs
                )
                
                # Record success
                latency_ms = result.get("latency_ms", 0)
                breaker.record_success(latency_ms)
                load_balancer.mark_request_end(model, attempt_provider, latency_ms, True)
                
                # Apply response transformations
                if not stream and "response" in result:
                    result["response"] = response_transformer.transform_response(
                        route_path,
                        result["response"],
                        context
                    )
                
                return result
                
            except CircuitBreakerOpenError as e:
                logger.warning("circuit_breaker_rejection", provider=attempt_provider)
                last_error = e
                continue
            except Exception as e:
                # Record failure
                breaker.record_failure(e)
                latency_ms = int((time.time() - start_time) * 1000)
                load_balancer.mark_request_end(model, attempt_provider, latency_ms, False)
                
                logger.error(
                    "provider_failure",
                    provider=attempt_provider,
                    error=str(e),
                    model=model
                )
                last_error = e
                continue
        
        # All providers failed
        logger.error("all_providers_failed", model=model, tried_providers=tried_providers)
        raise last_error or Exception("All providers failed")
    
    async def _execute_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
        provider: str,
        request_id: str,
        start_time: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute the actual completion request"""
        try:
            if provider == "mock":
                await asyncio.sleep(0.1)
                mock_response = self._generate_mock_response(messages, model)
                latency_ms = int((time.time() - start_time) * 1000)
                
                return {
                    "response": mock_response,
                    "request_id": request_id,
                    "provider": provider,
                    "model": model,
                    "prompt_tokens": mock_response["usage"]["prompt_tokens"],
                    "completion_tokens": mock_response["usage"]["completion_tokens"],
                    "total_tokens": mock_response["usage"]["total_tokens"],
                    "cost": 0.0,
                    "latency_ms": latency_ms
                }
            
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
            logger.error("execute_completion_error", model=model, provider=provider, error=str(e))
            raise
    
    def _select_provider_with_load_balancing(self, model: str) -> str:
        """Select provider using load balancer if configured, otherwise use default logic"""
        # Try load balancer first
        selected = load_balancer.select_provider(model)
        if selected:
            logger.debug("load_balancer_selected", model=model, provider=selected)
            return selected
        
        # Fallback to original logic
        return self.get_provider_for_model(model)
    
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
            if provider == "mock":
                import json
                mock_response = self._generate_mock_response(messages, model)
                content = mock_response["choices"][0]["message"]["content"]
                
                for word in content.split():
                    chunk = {
                        "id": mock_response["id"],
                        "object": "chat.completion.chunk",
                        "created": mock_response["created"],
                        "model": model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": word + " "},
                            "finish_reason": None
                        }]
                    }
                    chunk_json = json.dumps(chunk)
                    yield f"data: {chunk_json}\n\n"
                    await asyncio.sleep(0.05)
                
                yield "data: [DONE]\n\n"
                return
            
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
