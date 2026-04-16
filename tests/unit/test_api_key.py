"""
API Key 认证模块测试
"""
import pytest
import os

from app.core.auth.api_key import (
    APIKeyConfig,
    get_api_key_config,
    validate_api_key,
    generate_api_key,
    is_public_endpoint,
    PUBLIC_ENDPOINTS,
)


class TestAPIKeyConfig:
    """API Key 配置测试"""
    
    def test_create_config(self):
        """测试创建配置"""
        config = APIKeyConfig(
            enabled=True,
            valid_keys={"test-key"},
            header_name="X-API-Key",
        )
        
        assert config.enabled is True
        assert "test-key" in config.valid_keys
        assert config.header_name == "X-API-Key"


class TestValidateAPIKey:
    """API Key 验证测试"""
    
    def test_validate_with_valid_key(self, monkeypatch):
        """测试有效 key"""
        monkeypatch.setenv("API_KEY_ENABLED", "true")
        monkeypatch.setenv("API_KEYS", "valid-key-1,valid-key-2")
        
        # 清除缓存
        get_api_key_config.cache_clear()
        
        assert validate_api_key("valid-key-1") is True
        assert validate_api_key("valid-key-2") is True
    
    def test_validate_with_invalid_key(self, monkeypatch):
        """测试无效 key"""
        monkeypatch.setenv("API_KEY_ENABLED", "true")
        monkeypatch.setenv("API_KEYS", "valid-key")
        
        get_api_key_config.cache_clear()
        
        assert validate_api_key("invalid-key") is False
    
    def test_validate_with_empty_key(self, monkeypatch):
        """测试空 key"""
        monkeypatch.setenv("API_KEY_ENABLED", "true")
        monkeypatch.setenv("API_KEYS", "valid-key")
        
        get_api_key_config.cache_clear()
        
        assert validate_api_key("") is False
        assert validate_api_key(None) is False
    
    def test_validate_when_disabled(self, monkeypatch):
        """测试禁用认证时"""
        monkeypatch.setenv("API_KEY_ENABLED", "false")
        
        get_api_key_config.cache_clear()
        
        # 禁用时应始终通过
        assert validate_api_key(None) is True
        assert validate_api_key("any-key") is True


class TestGenerateAPIKey:
    """API Key 生成测试"""
    
    def test_generate_key(self):
        """测试生成 key"""
        key = generate_api_key()
        
        assert key is not None
        assert len(key) > 20  # token_urlsafe(32) 生成长度
    
    def test_generate_unique_keys(self):
        """测试生成唯一 key"""
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        assert key1 != key2


class TestPublicEndpoints:
    """公开端点测试"""
    
    def test_is_public_endpoint(self):
        """测试公开端点判断"""
        assert is_public_endpoint("/") is True
        assert is_public_endpoint("/health") is True
        assert is_public_endpoint("/metrics") is True
        assert is_public_endpoint("/docs") is True
    
    def test_is_not_public_endpoint(self):
        """测试非公开端点"""
        assert is_public_endpoint("/ask") is False
        assert is_public_endpoint("/schemas") is False
        assert is_public_endpoint("/admin") is False
    
    def test_public_endpoints_set(self):
        """测试公开端点集合"""
        assert "/" in PUBLIC_ENDPOINTS
        assert "/health" in PUBLIC_ENDPOINTS
        assert "/metrics" in PUBLIC_ENDPOINTS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
