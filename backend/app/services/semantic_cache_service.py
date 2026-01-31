import json
import hashlib
import time
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import structlog
import asyncio

from backend.app.core.config import settings

logger = structlog.get_logger()


class SemanticCacheService:
    def __init__(
        self,
        similarity_threshold: float = 0.92,
        ttl_seconds: int = 3600,
        max_cache_size: int = 10000,
        embedding_model: str = "text-embedding-3-small"
    ):
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.max_cache_size = max_cache_size
        self.embedding_model = embedding_model
        
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._embeddings_index: Dict[str, np.ndarray] = {}
        self._tenant_caches: Dict[int, List[str]] = {}
        
        self._redis = None
        self._use_redis = False
        
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "tokens_saved": 0,
            "cost_saved_usd": 0.0
        }
        
        logger.info(
            "semantic_cache_initialized",
            threshold=similarity_threshold,
            ttl=ttl_seconds,
            max_size=max_cache_size
        )
    
    async def init_redis(self):
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            pong = await self._redis.ping()
            if pong:
                self._use_redis = True
                logger.info("semantic_cache_redis_connected")
        except Exception as e:
            logger.warning("semantic_cache_redis_unavailable", error=str(e))
            self._use_redis = False
    
    def _compute_cache_key(self, messages: List[Dict[str, Any]], model: str) -> str:
        content = json.dumps({
            "messages": messages,
            "model": model
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _extract_prompt_text(self, messages: List[Dict[str, Any]]) -> str:
        texts = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                texts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        texts.append(item.get("text", ""))
        return " ".join(texts)
    
    async def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        try:
            from backend.app.services.router_service import router_service
            
            result = await router_service.embedding(
                model=self.embedding_model,
                input_text=text[:8000]
            )
            
            if result and "response" in result:
                embedding_data = result["response"].get("data", [])
                if embedding_data:
                    return np.array(embedding_data[0].get("embedding", []))
            
            return None
        except Exception as e:
            logger.warning("embedding_generation_failed", error=str(e))
            return None
    
    async def get_cached_response(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        tenant_id: int
    ) -> Optional[Dict[str, Any]]:
        cache_key = self._compute_cache_key(messages, model)
        
        cached = await self._get_from_cache(cache_key, tenant_id)
        if cached:
            self._stats["hits"] += 1
            logger.debug("cache_exact_hit", key=cache_key[:16])
            return cached
        
        prompt_text = self._extract_prompt_text(messages)
        query_embedding = await self._get_embedding(prompt_text)
        
        if query_embedding is None:
            self._stats["misses"] += 1
            return None
        
        similar_response = await self._find_similar(
            query_embedding,
            model,
            tenant_id
        )
        
        if similar_response:
            self._stats["hits"] += 1
            logger.debug("cache_semantic_hit", similarity=similar_response.get("similarity", 0))
            return similar_response
        
        self._stats["misses"] += 1
        return None
    
    async def _get_from_cache(
        self,
        cache_key: str,
        tenant_id: int
    ) -> Optional[Dict[str, Any]]:
        full_key = f"cache:{tenant_id}:{cache_key}"
        
        if self._use_redis and self._redis:
            try:
                data = await self._redis.get(full_key)
                if data:
                    cached = json.loads(data)
                    if time.time() < cached.get("expires_at", 0):
                        return cached.get("response")
            except Exception as e:
                logger.warning("redis_get_error", error=str(e))
        
        if full_key in self._cache:
            cached = self._cache[full_key]
            if time.time() < cached.get("expires_at", 0):
                return cached.get("response")
            else:
                del self._cache[full_key]
        
        return None
    
    async def _find_similar(
        self,
        query_embedding: np.ndarray,
        model: str,
        tenant_id: int
    ) -> Optional[Dict[str, Any]]:
        tenant_keys = self._tenant_caches.get(tenant_id, [])
        
        if not tenant_keys:
            return None
        
        best_match = None
        best_similarity = 0.0
        
        for key in tenant_keys:
            if key not in self._embeddings_index:
                continue
            
            cached_data = self._cache.get(key)
            if not cached_data:
                continue
            
            if cached_data.get("model") != model:
                continue
            
            if time.time() >= cached_data.get("expires_at", 0):
                continue
            
            cached_embedding = self._embeddings_index[key]
            
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                cached_embedding.reshape(1, -1)
            )[0][0]
            
            if similarity >= self.similarity_threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    **cached_data.get("response", {}),
                    "cache_hit": True,
                    "similarity": float(similarity)
                }
        
        return best_match
    
    async def cache_response(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        tenant_id: int,
        response: Dict[str, Any]
    ):
        cache_key = self._compute_cache_key(messages, model)
        full_key = f"cache:{tenant_id}:{cache_key}"
        
        prompt_text = self._extract_prompt_text(messages)
        embedding = await self._get_embedding(prompt_text)
        
        cache_entry = {
            "response": response,
            "model": model,
            "tenant_id": tenant_id,
            "created_at": time.time(),
            "expires_at": time.time() + self.ttl_seconds
        }
        
        if len(self._cache) >= self.max_cache_size:
            await self._evict_oldest()
        
        self._cache[full_key] = cache_entry
        
        if embedding is not None:
            self._embeddings_index[full_key] = embedding
        
        if tenant_id not in self._tenant_caches:
            self._tenant_caches[tenant_id] = []
        if full_key not in self._tenant_caches[tenant_id]:
            self._tenant_caches[tenant_id].append(full_key)
        
        if self._use_redis and self._redis:
            try:
                await self._redis.setex(
                    full_key,
                    self.ttl_seconds,
                    json.dumps(cache_entry, default=str)
                )
            except Exception as e:
                logger.warning("redis_set_error", error=str(e))
        
        logger.debug("response_cached", key=cache_key[:16], model=model)
    
    async def _evict_oldest(self):
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].get("created_at", 0)
        )
        
        del self._cache[oldest_key]
        
        if oldest_key in self._embeddings_index:
            del self._embeddings_index[oldest_key]
        
        for tenant_id, keys in self._tenant_caches.items():
            if oldest_key in keys:
                keys.remove(oldest_key)
        
        self._stats["evictions"] += 1
        logger.debug("cache_entry_evicted")
    
    async def invalidate_tenant_cache(self, tenant_id: int):
        keys_to_remove = self._tenant_caches.get(tenant_id, [])
        
        for key in keys_to_remove:
            if key in self._cache:
                del self._cache[key]
            if key in self._embeddings_index:
                del self._embeddings_index[key]
        
        self._tenant_caches[tenant_id] = []
        
        if self._use_redis and self._redis:
            try:
                pattern = f"cache:{tenant_id}:*"
                async for key in self._redis.scan_iter(match=pattern):
                    await self._redis.delete(key)
            except Exception as e:
                logger.warning("redis_invalidate_error", error=str(e))
        
        logger.info("tenant_cache_invalidated", tenant_id=tenant_id)
    
    def record_cache_savings(self, tokens_saved: int, cost_saved: float):
        """Record token and cost savings from a cache hit."""
        self._stats["tokens_saved"] += tokens_saved
        self._stats["cost_saved_usd"] += cost_saved
    
    def get_stats(self) -> Dict[str, Any]:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        
        USD_TO_INR = 83.5
        
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": round(hit_rate * 100, 2),
            "cache_size": len(self._cache),
            "embeddings_indexed": len(self._embeddings_index),
            "tenants_cached": len(self._tenant_caches),
            "tokens_saved": self._stats["tokens_saved"],
            "cost_saved_usd": round(self._stats["cost_saved_usd"], 4),
            "cost_saved_inr": round(self._stats["cost_saved_usd"] * USD_TO_INR, 2)
        }
    
    async def clear_all(self):
        self._cache.clear()
        self._embeddings_index.clear()
        self._tenant_caches.clear()
        
        if self._use_redis and self._redis:
            try:
                async for key in self._redis.scan_iter(match="cache:*"):
                    await self._redis.delete(key)
            except Exception as e:
                logger.warning("redis_clear_error", error=str(e))
        
        logger.info("cache_cleared")


semantic_cache = SemanticCacheService(
    similarity_threshold=0.92,
    ttl_seconds=3600,
    max_cache_size=10000
)
