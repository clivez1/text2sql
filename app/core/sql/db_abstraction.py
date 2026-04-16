"""
数据库抽象层 (Database Abstraction Layer)

提供统一的数据库访问接口，支持 SQLite / MySQL / PostgreSQL。

设计原则：
1. 统一接口 - 所有数据库操作通过 DatabaseManager 进行
2. 连接池管理 - 支持连接池和健康检查
3. 事务支持 - 提供上下文管理器进行事务操作
4. 可扩展性 - 易于添加新的数据库类型支持
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set, List, Dict, Any, Callable, Generator

import pandas as pd
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.exc import SQLAlchemyError


class DatabaseType(Enum):
    """支持的数据库类型"""
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"


@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_type: DatabaseType
    db_url: str
    host: str = "localhost"
    port: int = 0
    database: str = ""
    username: str = ""
    password: str = ""
    
    # 连接池配置
    pool_size: int = 5
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # 查询限制
    max_rows: int = 200
    query_timeout: int = 15
    
    # 安全配置
    readonly: bool = True
    
    @classmethod
    def from_url(cls, db_url: str, **kwargs) -> "DatabaseConfig":
        """从 URL 自动解析配置"""
        db_type = cls._detect_db_type(db_url)
        
        config = cls(
            db_type=db_type,
            db_url=db_url,
            **kwargs
        )
        
        # 解析 URL 提取连接信息
        if db_type != DatabaseType.SQLITE:
            config._parse_url_components(db_url)
        
        return config
    
    @staticmethod
    def _detect_db_type(db_url: str) -> DatabaseType:
        """从 URL 检测数据库类型"""
        url_lower = db_url.lower()
        if url_lower.startswith("sqlite"):
            return DatabaseType.SQLITE
        elif url_lower.startswith("mysql") or "mysql" in url_lower:
            return DatabaseType.MYSQL
        elif url_lower.startswith("postgresql") or url_lower.startswith("postgres"):
            return DatabaseType.POSTGRESQL
        raise ValueError(f"Cannot detect database type from URL: {db_url[:50]}...")
    
    def _parse_url_components(self, db_url: str) -> None:
        """解析 URL 组件"""
        # 格式: mysql+pymysql://user:pass@host:port/dbname
        try:
            # 提取用户名密码
            if "://" in db_url:
                auth_part = db_url.split("://")[1].split("@")[0]
                if ":" in auth_part:
                    self.username, self.password = auth_part.split(":", 1)
                
                # 提取主机端口数据库
                host_part = db_url.split("@")[1].split("/")[0]
                if ":" in host_part:
                    self.host, port_str = host_part.split(":", 1)
                    self.port = int(port_str)
                else:
                    self.host = host_part
                
                # 提取数据库名
                if "/" in db_url.split("@")[1]:
                    db_part = db_url.split("@")[1].split("/")[1]
                    self.database = db_part.split("?")[0]  # 移除查询参数
        except (IndexError, ValueError):
            pass  # 使用默认值


@dataclass
class QueryResult:
    """查询结果"""
    success: bool
    data: Optional[pd.DataFrame] = None
    row_count: int = 0
    columns: List[str] = field(default_factory=list)
    error: Optional[str] = None
    execution_time: float = 0.0
    truncated: bool = False


@dataclass
class HealthStatus:
    """健康检查状态"""
    is_healthy: bool
    db_type: str
    latency_ms: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


class DatabaseConnector(ABC):
    """数据库连接器抽象基类"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: Optional[Engine] = None
        self._is_connected: bool = False
    
    @property
    def engine(self) -> Engine:
        """获取数据库引擎（懒加载）"""
        if self._engine is None:
            self._engine = self._create_engine()
            self._setup_engine_events()
        return self._engine
    
    @abstractmethod
    def _create_engine(self) -> Engine:
        """创建数据库引擎"""
        ...
    
    def _setup_engine_events(self) -> None:
        """设置引擎事件监听"""
        @event.listens_for(self._engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            self._is_connected = True
            self._on_connect(dbapi_conn)
        
        @event.listens_for(self._engine, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            self._on_checkout(dbapi_conn)
    
    def _on_connect(self, dbapi_conn) -> None:
        """连接建立时的回调（子类可覆盖）"""
        pass
    
    def _on_checkout(self, dbapi_conn) -> None:
        """连接从池中取出时的回调（子类可覆盖）"""
        pass
    
    @abstractmethod
    def get_schema_info(self) -> str:
        """获取数据库结构信息（DDL格式）"""
        ...
    
    @abstractmethod
    def get_table_names(self) -> List[str]:
        """获取所有表名"""
        ...
    
    @abstractmethod
    def get_column_info(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        ...
    
    def execute_query(
        self, 
        sql: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """
        执行查询并返回结果
        
        Args:
            sql: SQL 查询语句
            params: 查询参数
            
        Returns:
            QueryResult: 查询结果
        """
        import time
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                # 设置查询超时（仅 PostgreSQL 支持）
                if self.config.query_timeout > 0 and self.config.db_type == DatabaseType.POSTGRESQL:
                    conn.execute(text(f"SET statement_timeout = {self.config.query_timeout * 1000}"))
                    conn.commit()
                
                # 执行查询
                result = pd.read_sql(
                    text(sql),
                    conn,
                    params=params
                )
            
            execution_time = time.time() - start_time
            row_count = len(result)
            
            # 检查是否需要截断
            truncated = False
            if row_count > self.config.max_rows:
                result = result.head(self.config.max_rows)
                truncated = True
            
            return QueryResult(
                success=True,
                data=result,
                row_count=min(row_count, self.config.max_rows),
                columns=list(result.columns),
                execution_time=execution_time,
                truncated=truncated
            )
            
        except SQLAlchemyError as e:
            return QueryResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def test_connection(self) -> HealthStatus:
        """测试数据库连接"""
        import time
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            latency = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=True,
                db_type=self.config.db_type.value,
                latency_ms=round(latency, 2),
                message="Connection successful"
            )
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=False,
                db_type=self.config.db_type.value,
                latency_ms=round(latency, 2),
                message=str(e)
            )
    
    def close(self) -> None:
        """关闭连接池"""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._is_connected = False
    
    def __enter__(self) -> "DatabaseConnector":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class DatabaseManager:
    """
    数据库管理器
    
    统一管理数据库连接，提供连接池、健康检查、事务管理等功能。
    """
    
    _instance: Optional["DatabaseManager"] = None
    _connectors: Dict[str, DatabaseConnector] = {}
    
    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_connector(self, name: str = "default") -> Optional[DatabaseConnector]:
        """获取指定名称的连接器"""
        return self._connectors.get(name)
    
    def register_connector(
        self, 
        connector: DatabaseConnector, 
        name: str = "default"
    ) -> None:
        """注册连接器"""
        self._connectors[name] = connector
    
    def create_connector(
        self, 
        config: DatabaseConfig,
        name: str = "default"
    ) -> DatabaseConnector:
        """创建并注册连接器"""
        from app.core.sql.connectors.sqlite import SQLiteConnector
        from app.core.sql.connectors.mysql import MySQLConnector
        from app.core.sql.connectors.postgresql import PostgreSQLConnector
        
        connector_map = {
            DatabaseType.SQLITE: SQLiteConnector,
            DatabaseType.MYSQL: MySQLConnector,
            DatabaseType.POSTGRESQL: PostgreSQLConnector,
        }
        
        connector_class = connector_map.get(config.db_type)
        if not connector_class:
            raise ValueError(f"Unsupported database type: {config.db_type}")
        
        connector = connector_class(config)
        self.register_connector(connector, name)
        return connector
    
    def execute(
        self, 
        sql: str, 
        connector_name: str = "default",
        params: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """执行查询"""
        connector = self.get_connector(connector_name)
        if not connector:
            return QueryResult(
                success=False,
                error=f"Connector '{connector_name}' not found"
            )
        return connector.execute_query(sql, params)
    
    def health_check(self, connector_name: str = "default") -> HealthStatus:
        """健康检查"""
        connector = self.get_connector(connector_name)
        if not connector:
            return HealthStatus(
                is_healthy=False,
                db_type="unknown",
                latency_ms=0,
                message=f"Connector '{connector_name}' not found"
            )
        return connector.test_connection()
    
    def close_all(self) -> None:
        """关闭所有连接"""
        for connector in self._connectors.values():
            connector.close()
        self._connectors.clear()
    
    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """获取单例实例"""
        return cls()
    
    def __del__(self) -> None:
        self.close_all()


# 便捷函数
def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    return DatabaseManager.get_instance()


def create_connector(config: DatabaseConfig, name: str = "default") -> DatabaseConnector:
    """创建数据库连接器"""
    manager = get_db_manager()
    return manager.create_connector(config, name)


def execute_query(
    sql: str, 
    config: Optional[DatabaseConfig] = None,
    connector_name: str = "default"
) -> QueryResult:
    """
    便捷查询执行函数
    
    Args:
        sql: SQL 查询语句
        config: 数据库配置（可选，如不提供则使用默认连接器）
        connector_name: 连接器名称
        
    Returns:
        QueryResult: 查询结果
    """
    manager = get_db_manager()
    
    # 如果提供了配置，创建新连接器
    if config:
        manager.create_connector(config, connector_name)
    
    return manager.execute(sql, connector_name)