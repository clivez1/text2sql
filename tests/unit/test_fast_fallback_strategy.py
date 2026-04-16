from app.core.llm import client
from app.core.llm import health_check


def test_simple_question_uses_rule_path(monkeypatch):
    called = {"adapter": False}

    class DummyAdapter:
        provider_name = "dummy"
        def generate_sql(self, question):
            called["adapter"] = True
            return "SELECT 1"

    monkeypatch.setattr(client, "get_llm_adapter", lambda: DummyAdapter())
    monkeypatch.setattr(client, "retrieve_schema_context", lambda question: "schema")
    sql, explanation, mode, blocked_reason = client.generate_sql("各城市订单数量")
    assert mode == "fallback"
    assert called["adapter"] is False
    assert "COUNT(*) AS order_count" in sql
    assert "fallback_ms" in explanation or "fast-fallback" in explanation


def test_list_products_uses_rule_path(monkeypatch):
    called = {"adapter": False}

    class DummyAdapter:
        provider_name = "dummy"
        def generate_sql(self, question):
            called["adapter"] = True
            return "SELECT 1"

    monkeypatch.setattr(client, "get_llm_adapter", lambda: DummyAdapter())
    monkeypatch.setattr(client, "retrieve_schema_context", lambda question: "schema")
    sql, explanation, mode, blocked_reason = client.generate_sql("列出所有产品")
    assert mode == "fallback"
    assert called["adapter"] is False
    assert "FROM products" in sql


def test_complex_question_can_still_try_llm(monkeypatch):
    called = {"adapter": False}

    class DummyAdapter:
        provider_name = "dummy"
        def generate_sql(self, question):
            called["adapter"] = True
            return "SELECT 1"

    monkeypatch.setattr(client, "get_llm_adapter", lambda: DummyAdapter())
    monkeypatch.setattr(client, "retrieve_schema_context", lambda question: "schema")
    # Mock 健康检查返回 LLM 可用
    monkeypatch.setattr(health_check, "should_use_fallback", lambda: False)
    sql, explanation, mode, blocked_reason = client.generate_sql("请结合上个月趋势分析销售额最高的前5个产品")
    assert called["adapter"] is True
