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
        """测试 LLM 提供商配置（N-provider 动态解析）"""
        settings = get_settings()

        # 验证新 N-provider 架构字段
        assert hasattr(settings, "_llm_providers")
        assert settings.provider_count >= 1

        # 验证 provider config 获取
        config = settings.get_provider_config(index=1)
        assert config.provider is not None
        assert config.api_key is not None
        assert config.model is not None

        # 验证 has_fallback
        assert hasattr(settings, "has_fallback")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
