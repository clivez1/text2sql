from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.core.sql.database import (
    DatabaseConfig,
    MySQLConnector,
    PostgreSQLConnector,
    SQLiteConnector,
    create_database_connector,
    _detect_db_type,
)


class DummySettings:
    db_url = "sqlite:///data/demo_db/sales.db"
    sql_max_rows = 123
    sql_query_timeout = 9
    readonly_mode = True


def test_detect_db_type_variants():
    assert _detect_db_type("sqlite:///tmp/test.db") == "sqlite"
    assert _detect_db_type("mysql+pymysql://u:p@h/db") == "mysql"
    assert _detect_db_type("postgresql://u:p@h/db") == "postgresql"
    assert _detect_db_type("postgres://u:p@h/db") == "postgresql"

    with pytest.raises(ValueError):
        _detect_db_type("oracle://example")


def test_sqlite_connector_create_engine_readonly_and_schema(monkeypatch):
    config = DatabaseConfig(db_type="sqlite", db_url="sqlite:///tmp/test.db", readonly=True)
    connector = SQLiteConnector(config)

    with patch("app.core.sql.database.create_engine", return_value="engine") as mocked:
        engine = connector._create_engine()
    assert engine == "engine"
    called_url = mocked.call_args.args[0]
    assert "mode=ro" in called_url
    assert "uri=true" in called_url

    monkeypatch.setattr(
        connector,
        "execute_query",
        lambda sql: pd.DataFrame([
            {"name": "orders", "sql": "CREATE TABLE orders(id INTEGER)"},
            {"name": "products", "sql": "CREATE TABLE products(id INTEGER)"},
        ]),
    )
    schema = connector.get_schema_info()
    assert "-- orders" in schema
    assert "CREATE TABLE products" in schema


def test_execute_query_and_test_connection_use_engine_head_limit():
    config = DatabaseConfig(db_type="sqlite", db_url="sqlite:///tmp/test.db", max_rows=1)
    connector = SQLiteConnector(config)

    fake_conn = MagicMock()
    fake_engine = MagicMock()
    fake_engine.connect.return_value.__enter__.return_value = fake_conn
    connector._engine = fake_engine

    with patch("app.core.sql.database.pd.read_sql", return_value=pd.DataFrame([{"id": 1}, {"id": 2}])):
        df = connector.execute_query("SELECT * FROM orders")
    assert len(df) == 1

    ok, message = connector.test_connection()
    assert ok is True
    assert "sqlite connection OK" == message


def test_test_connection_failure_returns_false():
    config = DatabaseConfig(db_type="sqlite", db_url="sqlite:///tmp/test.db")
    connector = SQLiteConnector(config)

    fake_engine = MagicMock()
    fake_engine.connect.side_effect = RuntimeError("db down")
    connector._engine = fake_engine

    ok, message = connector.test_connection()
    assert ok is False
    assert "db down" in message


def test_mysql_and_postgresql_schema_info(monkeypatch):
    mysql = MySQLConnector(DatabaseConfig(db_type="mysql", db_url="mysql+pymysql://u:p@h:3306/shop"))
    monkeypatch.setattr(
        mysql,
        "execute_query",
        lambda sql: pd.DataFrame([
            {"table_name": "orders", "column_name": "id", "column_type": "int", "is_nullable": "NO", "column_key": "PRI"},
            {"table_name": "orders", "column_name": "city", "column_type": "varchar(20)", "is_nullable": "YES", "column_key": ""},
        ]),
    )
    mysql_schema = mysql.get_schema_info()
    assert "CREATE TABLE orders" in mysql_schema
    assert "id int NOT NULL PRI" in mysql_schema

    pg = PostgreSQLConnector(DatabaseConfig(db_type="postgresql", db_url="postgresql://u:p@h:5432/shop"))
    monkeypatch.setattr(
        pg,
        "execute_query",
        lambda sql: pd.DataFrame([
            {"table_name": "products", "column_name": "id", "data_type": "integer", "is_nullable": "NO"},
            {"table_name": "products", "column_name": "name", "data_type": "text", "is_nullable": "YES"},
        ]),
    )
    pg_schema = pg.get_schema_info()
    assert "CREATE TABLE products" in pg_schema
    assert "id integer NOT NULL" in pg_schema


def test_create_database_connector_from_settings_and_explicit_config(monkeypatch):
    monkeypatch.setattr("app.core.sql.database.get_settings", lambda: DummySettings())
    connector = create_database_connector()
    assert isinstance(connector, SQLiteConnector)
    assert connector.config.max_rows == 123
    assert connector.config.query_timeout == 9

    explicit = create_database_connector(DatabaseConfig(db_type="mysql", db_url="mysql+pymysql://u:p@h/db"))
    assert isinstance(explicit, MySQLConnector)

    with pytest.raises(ValueError):
        create_database_connector(DatabaseConfig(db_type="oracle", db_url="oracle://x"))
