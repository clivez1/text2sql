"""
认证中间件

为 FastAPI 应用添加 API Key 认证。
"""
from __future__ import annotations

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.auth.api_key import validate_api_key, is_public_endpoint, get_api_key_config


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API Key 认证中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 检查是否为公开端点
        if is_public_endpoint(request.url.path):
            return await call_next(request)
        
        # 获取配置
        config = get_api_key_config()
        
        # 如果未启用认证，直接通过
        if not config.enabled:
            return await call_next(request)
        
        # 获取 API Key
        api_key = request.headers.get(config.header_name)
        
        # 验证
        if not validate_api_key(api_key):
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Invalid or missing API key",
                    "detail": f"Please provide a valid {config.header_name} header",
                }
            )
        
        return await call_next(request)
