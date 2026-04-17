import types
from pathlib import Path

from app.core.retrieval import schema_loader


def test_load_schema_text_reads_file(tmp_path, monkeypatch):
    project_root = tmp_path / "proj"
    ddl_dir = project_root / "data" / "ddl"
    ddl_dir.mkdir(parents=True)
    ddl_file = ddl_dir / "sales_schema.sql"
    ddl_file.write_text("CREATE TABLE orders(id INT);", encoding="utf-8")

    fake_file = project_root / "app" / "core" / "retrieval" / "schema_loader.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("# stub", encoding="utf-8")

    class FakePath(type(Path())):
        @classmethod
        def resolve(cls_self):
            return fake_file

    monkeypatch.setattr(schema_loader, "Path", FakePath)
    assert "CREATE TABLE orders" in schema_loader.load_schema_text()


def test_load_schema_documents_returns_empty_when_collection_missing(monkeypatch):
    class FakeClient:
        def get_collection(self, name):
            raise RuntimeError("missing")

    monkeypatch.setattr(schema_loader.chromadb, "PersistentClient", lambda path: FakeClient())
    docs = schema_loader.load_schema_documents()
    assert docs == []


def test_load_schema_documents_returns_documents(monkeypatch):
    class FakeCollection:
        def get(self, limit, include):
            return {
                "documents": ["doc1", "doc2"],
                "metadatas": [{"a": 1}, {"b": 2}],
            }

    class FakeClient:
        def get_collection(self, name):
            return FakeCollection()

    monkeypatch.setattr(schema_loader.chromadb, "PersistentClient", lambda path: FakeClient())
    docs = schema_loader.load_schema_documents()
    assert docs[0]["document"] == "doc1"
    assert docs[1]["metadata"] == {"b": 2}


def test_retrieve_schema_context_prefers_query_result(monkeypatch):
    class FakeRetriever:
        def retrieve(self, question, limit=4):
            return "orders(...)\n\nproducts(...)"

    monkeypatch.setattr(schema_loader, "_retriever_instance", None)
    monkeypatch.setattr(schema_loader, "get_retriever", lambda: FakeRetriever())
    result = schema_loader.retrieve_schema_context("订单和商品")
    assert "orders" in result and "products" in result


def test_retrieve_schema_context_falls_back_to_keyword_tables(monkeypatch):
    def failing_retriever():
        raise RuntimeError("boom")

    monkeypatch.setattr(schema_loader, "_retriever_instance", None)
    monkeypatch.setattr(schema_loader, "get_retriever", failing_retriever)
    monkeypatch.setattr(schema_loader, "load_schema_text", lambda: "DDL CONTENT")
    result = schema_loader.retrieve_schema_context("订单 商品 数量")
    assert "orders(" in result
    assert "products(" in result
    assert "order_items(" in result


def test_retrieve_schema_context_falls_back_to_ddl(monkeypatch):
    def failing_retriever():
        raise RuntimeError("boom")

    monkeypatch.setattr(schema_loader, "_retriever_instance", None)
    monkeypatch.setattr(schema_loader, "get_retriever", failing_retriever)
    monkeypatch.setattr(schema_loader, "load_schema_text", lambda: "X" * 2000)
    result = schema_loader.retrieve_schema_context("unrelated question")
    assert result == "X" * 1200
