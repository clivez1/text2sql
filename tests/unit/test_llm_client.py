import sys
from unittest.mock import MagicMock

# Mock chromadb before any transitive import
sys.modules.setdefault("chromadb", MagicMock())

from app.core.llm import client
from app.core.llm import health_check
from app.core.nlu.question_classifier import QuestionClassification
from app.core.retrieval import schema_loader


class DummyRetriever:
    def retrieve(self, question: str) -> str:
        return "schema"


class DummyAdapter:
    provider_name = "dummy"

    def generate_sql(self, question: str, schema_context: str | None = None) -> str:
        return "SELECT 1"

    def connectivity_check(self) -> str:
        return "ok"


class BrokenAdapter:
    provider_name = "broken"

    def generate_sql(self, question: str, schema_context: str | None = None) -> str:
        raise RuntimeError("llm down")

    def connectivity_check(self) -> str:
        return "fail"


def _complex_classification(q):
    return QuestionClassification(category="complex", needs_llm=True)


def test_generate_sql_success(monkeypatch):
    monkeypatch.setattr(client, "get_llm_adapter", lambda *a, **kw: DummyAdapter())
    monkeypatch.setattr(schema_loader, "get_retriever", lambda: DummyRetriever())
    monkeypatch.setattr(client, "classify_question", _complex_classification)
    monkeypatch.setattr(health_check, "should_use_fallback", lambda: False)
    sql, explanation, mode, blocked_reason = client.generate_sql("test")
    assert sql == "SELECT 1"
    assert mode == "dummy"
    assert blocked_reason is None


def test_generate_sql_fallback(monkeypatch):
    monkeypatch.setattr(client, "get_llm_adapter", lambda *a, **kw: BrokenAdapter())
    monkeypatch.setattr(schema_loader, "get_retriever", lambda: DummyRetriever())
    monkeypatch.setattr(client, "classify_question", _complex_classification)
    monkeypatch.setattr(
        client,
        "generate_sql_by_rules",
        lambda q: ("SELECT * FROM orders LIMIT 10", "rule fallback"),
    )
    monkeypatch.setattr(health_check, "should_use_fallback", lambda: False)
    sql, explanation, mode, blocked_reason = client.generate_sql("orders")
    assert mode == "fallback"
    assert "LLM runtime failed" in blocked_reason
    assert "SELECT * FROM orders" in sql


def test_check_llm_connectivity(monkeypatch):
    monkeypatch.setattr(client, "get_llm_adapter", lambda *a, **kw: DummyAdapter())
    monkeypatch.setattr(schema_loader, "get_retriever", lambda: DummyRetriever())
    provider, status = client.check_llm_connectivity()
    assert provider == "dummy"
    assert status == "ok"
