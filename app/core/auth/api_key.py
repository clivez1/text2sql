"""
API Key 认证模块

提供简单的 API Key 认证机制。
"""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from typing import Optional, Set
from functools import lru_cache


@dataclass
class APIKeyConfig:
    """API Key 配置"""
    enabled: bool
    valid_keys: Set[str]
    header_name: str = "X-API-Key"


@lru_cache()
def get_api_key_config() -> APIKeyConfig:
    """获取 API Key 配置"""
    # 从环境变量读取配置
    enabled = os.getenv("API_KEY_ENABLED", "false").lower() == "true"
    
    # 支持多个 API Key（逗号分隔）
    keys_str = os.getenv("API_KEYS", "")
    valid_keys = set()
    if keys_str:
        valid_keys = {k.strip() for k in keys_str.split(",") if k.strip()}
    
    # 如果没有配置，生成一个随机 key（仅用于开发）
    if enabled and not valid_keys:
        default_key = secrets.token_urlsafe(16)
        valid_keys = {default_key}
        # 输出到日志，方便开发使用
        import logging
        logging.getLogger(__name__).warning(
            f"No API_KEYS configured, generated default key: {default_key}"
        )
    
    header_name = os.getenv("API_KEY_HEADER", "X-API-Key")
    
    return APIKeyConfig(
        enabled=enabled,
        valid_keys=valid_keys,
        header_name=header_name,
    )


def validate_api_key(api_key: Optional[str]) -> bool:
    """验证 API Key"""
    config = get_api_key_config()
    
    # 如果未启用认证，直接通过
    if not config.enabled:
        return True
    
    # 如果启用但没有配置 key，允许通过（开发模式）
    if not config.valid_keys:
        return True
    
    # 验证 key
    if not api_key:
        return False
    
    return api_key in config.valid_keys


def generate_api_key() -> str:
    """生成新的 API Key"""
    return secrets.token_urlsafe(32)


# 不需要认证的端点
PUBLIC_ENDPOINTS = {
    "/",
    "/health",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
}


def is_public_endpoint(path: str) -> bool:
    """检查是否为公开端点"""
    # 精确匹配
    if path in PUBLIC_ENDPOINTS:
        return True
    
    # 前缀匹配（仅对文档端点）
    if path.startswith("/docs/") or path.startswith("/redoc/"):
        return True
    
    return False
