"""
配置模块测试
"""
import pytest
from app.config.settings import Settings, get_settings


class TestSettings:
    """配置测试"""
    
    def test_get_settings(self):
        """测试获取配置"""
        settings = get_settings()
        
        assert settings is not None
        assert hasattr(settings, "app_env")
    
    def test_settings_has_db_url(self):
        """测试数据库 URL 配置"""
        settings = get_settings()
        
        assert hasattr(settings, "db_url")
        assert settings.db_url is not None
    
    def test_settings_llm_provider(self):
        """测试 LLM 提供商配置"""
        settings = get_settings()
        
        assert hasattr(settings, "llm_provider")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])