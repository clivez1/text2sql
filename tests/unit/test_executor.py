import pandas as pd
import pytest

from app.core.sql.executor import QueryExecutor
from app.core.sql.db_abstraction import QueryResult, HealthStatus


class DummyDB:
    def execute_query(self, sql):
        df = pd.DataFrame([{"x": 1}])
        return QueryResult(success=True, data=df, row_count=1, columns=["x"])

    def test_connection(self):
        return HealthStatus(is_healthy=True, db_type="sqlite", latency_ms=0.0, message="ok")

    def get_schema_info(self):
        return "schema"


class BrokenDB(DummyDB):
    def execute_query(self, sql):
        raise RuntimeError("db error")


class DummyValidator:
    pass


def test_execute_with_validation(monkeypatch):
    monkeypatch.setattr("app.core.sql.executor.validate_readonly_sql", lambda sql: "SELECT 1 LIMIT 10")
    executor = QueryExecutor(db_connector=DummyDB(), validator=DummyValidator())
    df = executor.execute("SELECT 1")
    assert not df.empty


def test_execute_without_validation():
    executor = QueryExecutor(db_connector=DummyDB(), validator=DummyValidator())
    df = executor.execute("SELECT 1", validate=False)
    assert not df.empty


def test_execute_raises_on_db_error(monkeypatch):
    monkeypatch.setattr("app.core.sql.executor.validate_readonly_sql", lambda sql: sql)
    executor = QueryExecutor(db_connector=BrokenDB(), validator=DummyValidator())
    with pytest.raises(RuntimeError):
        executor.execute("SELECT 1")


def test_test_connection_and_schema_info():
    executor = QueryExecutor(db_connector=DummyDB(), validator=DummyValidator())
    assert executor.test_connection() == (True, "ok")
    assert executor.get_schema_info() == "schema"
