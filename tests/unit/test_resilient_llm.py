from app.core.llm.resilient_llm import (
    ResilienceConfig,
    ResilientVannaClient,
    get_resilient_vanna,
    reset_resilient_client,
)


class StubVanna:
    def __init__(self, sql="SELECT 1", ddl=None, fail_generate=None, fail_ddl=None, training_error=None):
        self.sql = sql
        self.ddl = ddl if ddl is not None else ["CREATE TABLE products (...)"]
        self.fail_generate = fail_generate
        self.fail_ddl = fail_ddl
        self.training_error = training_error

    def generate_sql(self, question, **kwargs):
        if self.fail_generate:
            raise self.fail_generate
        return self.sql

    def get_related_ddl(self, question, **kwargs):
        if self.fail_ddl:
            raise self.fail_ddl
        return self.ddl

    def get_training_data(self):
        if self.training_error:
            raise self.training_error
        return [{"id": 1}]


class LastAttempt:
    def __init__(self, exc):
        self._exc = exc

    def exception(self):
        return self._exc


class FakeRetryError(ConnectionError):
    def __init__(self, exc):
        super().__init__(str(exc))
        self.last_attempt = LastAttempt(exc)


def test_generate_sql_success(monkeypatch):
    client = ResilientVannaClient(StubVanna(sql="SELECT * FROM products"))
    monkeypatch.setattr(client, "_generate_sql_with_retry", lambda question, **kwargs: "SELECT * FROM products")

    assert client.generate_sql("列出产品") == "SELECT * FROM products"


def test_generate_sql_falls_back_to_rule_sql(monkeypatch):
    client = ResilientVannaClient(StubVanna())
    monkeypatch.setattr(
        client,
        "_generate_sql_with_retry",
        lambda question, **kwargs: (_ for _ in ()).throw(FakeRetryError(ConnectionError("boom"))),
    )

    result = client.generate_sql("产品数量")
    assert "COUNT(*) AS count FROM products" in result


def test_handle_failure_uses_template_when_needed(monkeypatch):
    client = ResilientVannaClient(
        StubVanna(),
        config=ResilienceConfig(fallback_enabled=True, fallback_sql_template="SELECT 7"),
    )
    monkeypatch.setattr(client, "_try_rule_based_fallback", lambda question: None)

    assert client._handle_sql_failure("未知问题", RuntimeError("x")) == "SELECT 7"


def test_get_related_ddl_and_connectivity():
    ok_client = ResilientVannaClient(StubVanna())
    bad_client = ResilientVannaClient(StubVanna(training_error=RuntimeError("x")))

    assert ok_client.get_related_ddl("products") == ["CREATE TABLE products (...)"]
    assert ok_client.connectivity_check() is True
    assert bad_client.connectivity_check() is False


def test_get_related_ddl_returns_empty_when_retry_fails(monkeypatch):
    client = ResilientVannaClient(StubVanna())
    monkeypatch.setattr(
        client,
        "_get_ddl_with_retry",
        lambda question, **kwargs: (_ for _ in ()).throw(RuntimeError("ddl failed")),
    )

    assert client.get_related_ddl("products") == []


def test_global_cache_behaviour():
    reset_resilient_client()
    first = get_resilient_vanna(vanna_instance=StubVanna(sql="SELECT 1"))
    second = get_resilient_vanna(vanna_instance=StubVanna(sql="SELECT 2"))
    assert first is second

    reset_resilient_client()
    third = get_resilient_vanna(vanna_instance=StubVanna(sql="SELECT 3"))
    assert third is not first
