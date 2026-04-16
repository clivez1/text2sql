from app.core.llm import client
from app.core.llm import health_check


class DummyAdapter:
    provider_name = "dummy"

    def generate_sql(self, question: str) -> str:
        return "SELECT 1"

    def connectivity_check(self) -> str:
        return "ok"


class BrokenAdapter:
    provider_name = "broken"

    def generate_sql(self, question: str) -> str:
        raise RuntimeError("llm down")

    def connectivity_check(self) -> str:
        return "fail"


def test_generate_sql_success(monkeypatch):
    monkeypatch.setattr(client, "get_llm_adapter", lambda: DummyAdapter())
    monkeypatch.setattr(client, "retrieve_schema_context", lambda question: "schema")
    # Mock 健康检查返回 LLM 可用
    monkeypatch.setattr(health_check, "should_use_fallback", lambda: False)
    sql, explanation, mode, blocked_reason = client.generate_sql("test")
    assert sql == "SELECT 1"
    assert mode == "dummy"
    assert blocked_reason is None


def test_generate_sql_fallback(monkeypatch):
    monkeypatch.setattr(client, "get_llm_adapter", lambda: BrokenAdapter())
    monkeypatch.setattr(client, "retrieve_schema_context", lambda question: "schema ctx")
    monkeypatch.setattr(client, "generate_sql_by_rules", lambda q: ("SELECT * FROM orders LIMIT 10", "rule fallback"))
    # Mock 健康检查返回 LLM 可用
    monkeypatch.setattr(health_check, "should_use_fallback", lambda: False)
    sql, explanation, mode, blocked_reason = client.generate_sql("orders")
    assert mode == "fallback"
    assert "LLM runtime failed" in blocked_reason
    assert "SELECT * FROM orders" in sql


def test_check_llm_connectivity(monkeypatch):
    monkeypatch.setattr(client, "get_llm_adapter", lambda: DummyAdapter())
    provider, status = client.check_llm_connectivity()
    assert provider == "dummy"
    assert status == "ok"
