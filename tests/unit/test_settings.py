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
        """测试 LLM 提供商配置（现在通过 URL 自动检测 provider）"""
        settings = get_settings()

        # 验证新配置字段存在
        assert hasattr(settings, "llm_api_key")
        assert hasattr(settings, "llm_base_url")
        assert hasattr(settings, "llm_model")

        # 验证 provider 自动检测功能
        config = settings.get_provider_config(index=1)
        assert config.provider in ("openai_compatible", "anthropic")
        assert config.api_key == settings.llm_api_key
        assert config.base_url == settings.llm_base_url
        assert config.model == settings.llm_model

        # 验证 has_fallback
        assert hasattr(settings, "has_fallback")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
