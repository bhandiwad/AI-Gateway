import redis.asyncio as redis
from typing import Optional
import time

from backend.app.core.config import settings


class RateLimiter:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def init(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
        except Exception:
            self.redis_client = None
    
    async def close(self):
        if self.redis_client:
            await self.redis_client.close()
    
    async def is_rate_limited(
        self,
        key: str,
        limit: int = None,
        window: int = None
    ) -> tuple[bool, int, int]:
        if not settings.ENABLE_RATE_LIMITING or not self.redis_client:
            return False, 0, limit or settings.DEFAULT_RATE_LIMIT
        
        limit = limit or settings.DEFAULT_RATE_LIMIT
        window = window or settings.RATE_LIMIT_WINDOW_SECONDS
        
        current_time = int(time.time())
        window_start = current_time - window
        
        rate_key = f"rate_limit:{key}"
        
        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(rate_key, 0, window_start)
            pipe.zadd(rate_key, {str(current_time): current_time})
            pipe.zcard(rate_key)
            pipe.expire(rate_key, window)
            results = await pipe.execute()
            
            current_count = results[2]
            remaining = max(0, limit - current_count)
            
            return current_count > limit, current_count, remaining
        except Exception:
            return False, 0, limit
    
    async def get_usage(self, key: str) -> int:
        if not self.redis_client:
            return 0
        
        try:
            rate_key = f"rate_limit:{key}"
            return await self.redis_client.zcard(rate_key)
        except Exception:
            return 0


rate_limiter = RateLimiter()
