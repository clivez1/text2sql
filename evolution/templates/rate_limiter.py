"""
请求限流中间件

基于令牌桶算法的内存限流器，支持单 IP 限流。
直接复用自 Data Viz Agent，无需修改。
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from threading import Lock

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


@dataclass
class TokenBucket:
    """令牌桶"""
    capacity: int  # 桶容量
    tokens: float = field(default=0.0)  # 当前令牌数
    last_refill: float = field(default_factory=time.time)  # 上次填充时间
    refill_rate: float = field(default=1.0)  # 令牌填充速率（个/秒）
    
    def __post_init__(self):
        if self.tokens == 0.0:
            self.tokens = float(self.capacity)
    
    def consume(self, tokens: int = 1) -> bool:
        """消费令牌"""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self) -> None:
        """填充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now


@dataclass
class RateLimiterConfig:
    """限流配置"""
    requests_per_minute: int = 60
    burst_size: int = 10  # 突发流量上限
    cleanup_interval: int = 300  # 清理间隔（秒）
    exempt_paths: list = field(default_factory=lambda: ["/health", "/ready", "/schemas"])


class RateLimiter:
    """
    内存限流器
    
    使用令牌桶算法实现，支持按 IP 限流。
    """
    
    def __init__(self, config: Optional[RateLimiterConfig] = None):
        self.config = config or RateLimiterConfig()
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()
        self._refill_rate = self.config.requests_per_minute / 60.0
    
    def is_allowed(self, client_id: str) -> bool:
        """检查是否允许请求"""
        with self._lock:
            self._cleanup_if_needed()
            
            bucket = self._buckets.get(client_id)
            if bucket is None:
                bucket = TokenBucket(
                    capacity=self.config.burst_size,
                    refill_rate=self._refill_rate,
                )
                self._buckets[client_id] = bucket
            
            return bucket.consume()
    
    def get_remaining(self, client_id: str) -> int:
        """获取剩余请求数"""
        with self._lock:
            bucket = self._buckets.get(client_id)
            if bucket is None:
                return self.config.burst_size
            bucket._refill()
            return int(bucket.tokens)
    
    def _cleanup_if_needed(self) -> None:
        """定期清理过期桶"""
        now = time.time()
        if now - self._last_cleanup < self.config.cleanup_interval:
            return
        
        cutoff = now - 300
        expired = [
            client_id for client_id, bucket in self._buckets.items()
            if bucket.last_refill < cutoff
        ]
        for client_id in expired:
            del self._buckets[client_id]
        
        self._last_cleanup = now
        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired rate limit buckets")


# 全局限流器实例
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(config: Optional[RateLimiterConfig] = None) -> RateLimiter:
    """获取全局限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(config)
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI 限流中间件"""
    
    def __init__(self, app, config: Optional[RateLimiterConfig] = None):
        super().__init__(app)
        self.limiter = RateLimiter(config)
    
    async def dispatch(self, request: Request, call_next):
        # 跳过豁免路径
        if request.url.path in self.limiter.config.exempt_paths:
            return await call_next(request)
        
        # 获取客户端 IP
        client_id = self._get_client_id(request)
        
        # 检查限流
        if not self.limiter.is_allowed(client_id):
            remaining = self.limiter.get_remaining(client_id)
            logger.warning(f"Rate limit exceeded for {client_id}")
            
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": 3003,
                        "message": "请求过于频繁，请稍后重试",
                        "detail": f"剩余请求数: {remaining}",
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(self.limiter.config.requests_per_minute),
                    "X-RateLimit-Remaining": str(remaining),
                    "Retry-After": "60",
                }
            )
        
        response = await call_next(request)
        
        remaining = self.limiter.get_remaining(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"


def rate_limit_middleware(
    app,
    requests_per_minute: int = 60,
    burst_size: int = 10,
) -> None:
    """添加限流中间件（便捷函数）"""
    config = RateLimiterConfig(
        requests_per_minute=requests_per_minute,
        burst_size=burst_size,
    )
    app.add_middleware(RateLimitMiddleware, config=config)