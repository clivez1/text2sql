"""
LLM 弹性客户端测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.core.llm.resilient_client import ResilientVannaClient, ResilienceConfig


class TestResilienceConfig:
    """弹性配置测试"""
    
    def test_create_config(self):
        """测试创建配置"""
        config = ResilienceConfig(
            max_retries=3,
            timeout_seconds=30.0,
        )
        
        assert config.max_retries == 3
        assert config.timeout_seconds == 30.0
    
    def test_config_defaults(self):
        """测试配置默认值"""
        config = ResilienceConfig()
        
        assert config.max_retries == 3
        assert config.timeout_seconds == 30.0
        assert config.fallback_enabled is True


class TestResilientVannaClient:
    """弹性 Vanna 客户端测试"""
    
    @pytest.fixture
    def config(self):
        return ResilienceConfig(max_retries=2, timeout_seconds=10.0)
    
    @pytest.fixture
    def mock_vanna(self):
        return MagicMock()
    
    def test_create_client(self, mock_vanna, config):
        """测试创建客户端"""
        client = ResilientVannaClient(mock_vanna, config)
        
        assert client.config == config
        assert client.vanna == mock_vanna
    
    def test_generate_sql_success(self, mock_vanna, config):
        """测试成功生成 SQL"""
        mock_vanna.generate_sql.return_value = "SELECT 1"
        
        client = ResilientVannaClient(mock_vanna, config)
        result = client.generate_sql("查询订单")
        
        assert result == "SELECT 1"

    def test_rule_based_fallback_branches(self, mock_vanna):
        client = ResilientVannaClient(mock_vanna, ResilienceConfig())
        assert "COUNT(*)" in client._try_rule_based_fallback("订单数量")
        assert "products" in client._try_rule_based_fallback("列出所有产品")
        assert client._try_rule_based_fallback("完全未知问题") is None

    def test_handle_sql_failure_uses_template(self, mock_vanna):
        config = ResilienceConfig(
            max_retries=1,
            fallback_enabled=False,
            fallback_sql_template="SELECT 1 AS fallback",
        )
        client = ResilientVannaClient(mock_vanna, config)
        assert client._handle_sql_failure("查询订单", RuntimeError("x")) == "SELECT 1 AS fallback"

    def test_get_related_ddl_and_connectivity(self, mock_vanna, config):
        mock_vanna.get_related_ddl.return_value = ["CREATE TABLE orders (...)"]
        mock_vanna.get_training_data.return_value = [{"id": 1}]
        client = ResilientVannaClient(mock_vanna, config)
        assert client.get_related_ddl("订单") == ["CREATE TABLE orders (...)"]
        assert client.connectivity_check() is True

    def test_get_related_ddl_failure_returns_empty(self, mock_vanna, config, monkeypatch):
        client = ResilientVannaClient(mock_vanna, config)
        monkeypatch.setattr(client, "_get_ddl_with_retry", lambda question, **kwargs: (_ for _ in ()).throw(RuntimeError("ddl failed")))
        assert client.get_related_ddl("订单") == []

    def test_connectivity_check_failure(self, mock_vanna, config):
        mock_vanna.get_training_data.side_effect = RuntimeError("down")
        client = ResilientVannaClient(mock_vanna, config)
        assert client.connectivity_check() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])