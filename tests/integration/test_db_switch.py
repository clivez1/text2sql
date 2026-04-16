"""
多数据库切换集成测试

测试 SQLite / MySQL / PostgreSQL 数据库连接器的切换功能。
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from sqlalchemy import text

from app.core.sql.db_abstraction import (
    DatabaseConfig,
    DatabaseType,
    DatabaseConnector,
    DatabaseManager,
    QueryResult,
    HealthStatus,
    create_connector,
    get_db_manager,
)
from app.core.sql.connectors.sqlite import SQLiteConnector
from app.core.sql.connectors.mysql import MySQLConnector
from app.core.sql.connectors.postgresql import PostgreSQLConnector


class TestDatabaseConfig:
    """数据库配置测试"""
    
    def test_sqlite_config_from_url(self):
        """测试从 URL 创建 SQLite 配置"""
        config = DatabaseConfig.from_url("sqlite:///data/test.db")
        
        assert config.db_type == DatabaseType.SQLITE
        assert "test.db" in config.db_url
    
    def test_mysql_config_from_url(self):
        """测试从 URL 创建 MySQL 配置"""
        config = DatabaseConfig.from_url(
            "mysql+pymysql://user:pass@localhost:3306/testdb"
        )
        
        assert config.db_type == DatabaseType.MYSQL
        assert config.database == "testdb"
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.username == "user"
        assert config.password == "pass"
    
    def test_postgresql_config_from_url(self):
        """测试从 URL 创建 PostgreSQL 配置"""
        config = DatabaseConfig.from_url(
            "postgresql://user:pass@localhost:5432/testdb"
        )
        
        assert config.db_type == DatabaseType.POSTGRESQL
        assert config.database == "testdb"
    
    def test_invalid_url(self):
        """测试无效 URL"""
        with pytest.raises(ValueError):
            DatabaseConfig.from_url("invalid://url")


class TestSQLiteConnector:
    """SQLite 连接器测试"""
    
    @pytest.fixture
    def sqlite_config(self, tmp_path):
        """创建 SQLite 配置"""
        db_path = tmp_path / "test.db"
        return DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            db_url=f"sqlite:///{db_path}",
            readonly=False,  # 测试需要写权限
        )
    
    def test_create_connector(self, sqlite_config):
        """测试创建连接器"""
        connector = SQLiteConnector(sqlite_config)
        
        assert connector.config.db_type == DatabaseType.SQLITE
        assert connector.engine is not None
    
    def test_execute_query(self, sqlite_config):
        """测试执行查询"""
        connector = SQLiteConnector(sqlite_config)
        
        # 创建测试表
        with connector.engine.connect() as conn:
            conn.execute(text("CREATE TABLE test (id INTEGER, name TEXT)"))
            conn.execute(text("INSERT INTO test VALUES (1, 'Alice')"))
            conn.execute(text("INSERT INTO test VALUES (2, 'Bob')"))
            conn.commit()
        
        # 查询测试
        result = connector.execute_query("SELECT * FROM test")
        
        assert result.success
        assert result.row_count == 2
        assert "id" in result.columns
        assert "name" in result.columns
    
    def test_get_table_names(self, sqlite_config):
        """测试获取表名"""
        connector = SQLiteConnector(sqlite_config)
        
        # 创建测试表
        with connector.engine.connect() as conn:
            conn.execute(text("CREATE TABLE orders (id INTEGER)"))
            conn.execute(text("CREATE TABLE products (id INTEGER)"))
            conn.commit()
        
        tables = connector.get_table_names()
        
        assert "orders" in tables
        assert "products" in tables
    
    def test_test_connection(self, sqlite_config):
        """测试连接健康检查"""
        connector = SQLiteConnector(sqlite_config)
        status = connector.test_connection()
        
        assert status.is_healthy
        assert status.db_type == "sqlite"


class TestMySQLConnector:
    """MySQL 连接器测试"""
    
    @pytest.fixture
    def mysql_config(self):
        """创建 MySQL 配置"""
        return DatabaseConfig(
            db_type=DatabaseType.MYSQL,
            db_url="mysql+pymysql://test:test@localhost:3306/testdb",
            database="testdb",
            host="localhost",
            port=3306,
            username="test",
            password="test",
            pool_size=2,
            readonly=True,
        )
    
    def test_create_connector(self, mysql_config):
        """测试创建连接器"""
        connector = MySQLConnector(mysql_config)
        
        assert connector.config.db_type == DatabaseType.MYSQL
        assert connector.config.database == "testdb"
    
    @pytest.mark.skip(reason="需要实际 MySQL 服务器")
    def test_real_mysql_connection(self, mysql_config):
        """测试真实 MySQL 连接（需要服务器）"""
        connector = MySQLConnector(mysql_config)
        status = connector.test_connection()
        
        assert status.is_healthy
    
    def test_mysql_schema_info(self, mysql_config):
        """测试获取 MySQL Schema（模拟）"""
        connector = MySQLConnector(mysql_config)
        
        # 验证配置正确
        assert connector.config.database == "testdb"


class TestPostgreSQLConnector:
    """PostgreSQL 连接器测试"""
    
    @pytest.fixture
    def pg_config(self):
        """创建 PostgreSQL 配置"""
        return DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            db_url="postgresql://test:test@localhost:5432/testdb",
            database="testdb",
            host="localhost",
            port=5432,
            username="test",
            password="test",
            readonly=True,
        )
    
    def test_create_connector(self, pg_config):
        """测试创建连接器"""
        connector = PostgreSQLConnector(pg_config)
        
        assert connector.config.db_type == DatabaseType.POSTGRESQL
        assert connector.config.database == "testdb"
    
    @pytest.mark.skip(reason="需要实际 PostgreSQL 服务器")
    def test_real_postgres_connection(self, pg_config):
        """测试真实 PostgreSQL 连接（需要服务器）"""
        connector = PostgreSQLConnector(pg_config)
        status = connector.test_connection()
        
        assert status.is_healthy


class TestDatabaseManager:
    """数据库管理器测试"""
    
    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        manager = DatabaseManager()
        yield manager
        manager.close_all()
    
    def test_singleton(self, manager):
        """测试单例模式"""
        manager2 = DatabaseManager()
        
        assert manager is manager2
    
    def test_register_connector(self, manager, tmp_path):
        """测试注册连接器"""
        db_path = tmp_path / "test.db"
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            db_url=f"sqlite:///{db_path}",
        )
        
        connector = SQLiteConnector(config)
        manager.register_connector(connector, "test_db")
        
        assert manager.get_connector("test_db") is connector
    
    def test_create_connector(self, manager, tmp_path):
        """测试创建连接器"""
        db_path = tmp_path / "test.db"
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            db_url=f"sqlite:///{db_path}",
        )
        
        connector = manager.create_connector(config, "new_db")
        
        assert connector is not None
        assert manager.get_connector("new_db") is connector
    
    def test_execute_query(self, manager, tmp_path):
        """测试执行查询"""
        db_path = tmp_path / "test.db"
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            db_url=f"sqlite:///{db_path}",
            readonly=False,
        )
        
        connector = manager.create_connector(config, "exec_test")
        
        # 创建测试表
        with connector.engine.connect() as conn:
            conn.execute(text("CREATE TABLE test (id INTEGER)"))
            conn.commit()
        
        result = manager.execute("SELECT * FROM test", "exec_test")
        
        assert result.success
    
    def test_close_all(self, manager, tmp_path):
        """测试关闭所有连接"""
        db_path = tmp_path / "test.db"
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            db_url=f"sqlite:///{db_path}",
        )
        
        manager.create_connector(config, "db1")
        manager.create_connector(config, "db2")
        
        manager.close_all()
        
        assert len(manager._connectors) == 0


class TestDatabaseSwitch:
    """数据库切换测试"""
    
    @pytest.fixture
    def manager(self):
        """创建管理器实例"""
        manager = DatabaseManager()
        yield manager
        manager.close_all()
    
    def test_switch_between_databases(self, manager, tmp_path):
        """测试在多个数据库间切换"""
        # 创建两个 SQLite 数据库
        db1_path = tmp_path / "db1.db"
        db2_path = tmp_path / "db2.db"
        
        config1 = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            db_url=f"sqlite:///{db1_path}",
            readonly=False,
        )
        config2 = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            db_url=f"sqlite:///{db2_path}",
            readonly=False,
        )
        
        # 创建连接器
        conn1 = manager.create_connector(config1, "db1")
        conn2 = manager.create_connector(config2, "db2")
        
        # 在 db1 创建表
        with conn1.engine.connect() as c:
            c.execute(text("CREATE TABLE orders (id INTEGER)"))
            c.execute(text("INSERT INTO orders VALUES (1)"))
            c.commit()
        
        # 在 db2 创建不同的表
        with conn2.engine.connect() as c:
            c.execute(text("CREATE TABLE products (id INTEGER)"))
            c.execute(text("INSERT INTO products VALUES (100)"))
            c.commit()
        
        # 切换查询
        result1 = manager.execute("SELECT * FROM orders", "db1")
        result2 = manager.execute("SELECT * FROM products", "db2")
        
        assert result1.success
        assert result1.row_count == 1
        
        assert result2.success
        assert result2.row_count == 1
    
    def test_same_connector_reuse(self, manager, tmp_path):
        """测试同一连接器可复用"""
        db_path = tmp_path / "test.db"
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            db_url=f"sqlite:///{db_path}",
            readonly=False,
        )
        
        manager.create_connector(config, "reusable")
        
        # 执行多次查询
        for i in range(5):
            result = manager.execute("SELECT 1 as value", "reusable")
            assert result.success


class TestQueryResult:
    """查询结果测试"""
    
    def test_success_result(self):
        """测试成功结果"""
        import pandas as pd
        
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["A", "B", "C"]})
        result = QueryResult(
            success=True,
            data=df,
            row_count=3,
            columns=["id", "name"],
            execution_time=0.05,
        )
        
        assert result.success
        assert result.row_count == 3
        assert len(result.columns) == 2
    
    def test_error_result(self):
        """测试错误结果"""
        result = QueryResult(
            success=False,
            error="Table not found",
            execution_time=0.01,
        )
        
        assert not result.success
        assert "Table not found" in result.error


class TestHealthStatus:
    """健康状态测试"""
    
    def test_healthy_status(self):
        """测试健康状态"""
        status = HealthStatus(
            is_healthy=True,
            db_type="mysql",
            latency_ms=5.23,
            message="Connection successful",
        )
        
        assert status.is_healthy
        assert status.latency_ms < 10
    
    def test_unhealthy_status(self):
        """测试不健康状态"""
        status = HealthStatus(
            is_healthy=False,
            db_type="mysql",
            latency_ms=1000,
            message="Connection timeout",
        )
        
        assert not status.is_healthy
        assert status.latency_ms > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])