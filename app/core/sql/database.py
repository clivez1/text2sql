"""
废弃模块，请使用 db_abstraction.py

此文件已废弃，所有功能已迁移到 db_abstraction.py。
此文件将在所有调用点迁移完成后删除。

迁移说明：
- create_database_connector() → 使用 db_abstraction.DatabaseConfig.from_url() + db_abstraction.create_connector()
- DatabaseConnector → db_abstraction.DatabaseConnector（接口兼容）
- execute_query() → db_abstraction.connector.execute_query() 返回 QueryResult，需取 .data 字段
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config.settings import get_settings


@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_type: str  # sqlite, mysql, postgresql
    db_url: str
    max_rows: int = 200
    query_timeout: int = 15
    readonly: bool = True


class DatabaseConnector(ABC):
    """数据库连接器抽象基类"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: Optional[Engine] = None
    
    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @abstractmethod
    def _create_engine(self) -> Engine:
        """创建数据库引擎"""
        ...
    
    @abstractmethod
    def get_schema_info(self) -> str:
        """获取数据库结构信息"""
        ...
    
    def execute_query(self, sql: str) -> pd.DataFrame:
        """执行查询并返回 DataFrame"""
        with self.engine.connect() as conn:
            df = pd.read_sql(text(sql), conn)
        return df.head(self.config.max_rows)
    
    def test_connection(self) -> tuple[bool, str]:
        """测试数据库连接"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, f"{self.config.db_type} connection OK"
        except Exception as e:
            return False, str(e)


class SQLiteConnector(DatabaseConnector):
    """SQLite 数据库连接器"""
    
    def _create_engine(self) -> Engine:
        # SQLite 只读模式
        url = self.config.db_url
        if self.config.readonly and "mode=" not in url:
            url = url.replace("sqlite:///", "sqlite:///file:") + "?mode=ro&uri=true"
        return create_engine(url)
    
    def get_schema_info(self) -> str:
        sql = """
        SELECT name, sql FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
        """
        df = self.execute_query(sql)
        return "\n\n".join(f"-- {row['name']}\n{row['sql']}" for _, row in df.iterrows())


class MySQLConnector(DatabaseConnector):
    """MySQL 数据库连接器"""
    
    def _create_engine(self) -> Engine:
        return create_engine(
            self.config.db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 10}
        )
    
    def get_schema_info(self) -> str:
        # 从 URL 提取数据库名
        db_name = self.config.db_url.split("/")[-1].split("?")[0]
        sql = f"""
        SELECT table_name, column_name, column_type, is_nullable, column_key
        FROM information_schema.columns
        WHERE table_schema = '{db_name}'
        ORDER BY table_name, ordinal_position;
        """
        df = self.execute_query(sql)
        
        # 按表分组生成 DDL 风格描述
        tables = df.groupby("table_name")
        lines = []
        for table_name, group in tables:
            lines.append(f"-- {table_name}")
            cols = []
            for _, row in group.iterrows():
                nullable = "" if row["is_nullable"] == "YES" else " NOT NULL"
                key = f" {row['column_key']}" if row["column_key"] else ""
                cols.append(f"  {row['column_name']} {row['column_type']}{nullable}{key}")
            lines.append("CREATE TABLE " + table_name + " (\n" + ",\n".join(cols) + "\n);")
        return "\n\n".join(lines)


class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL 数据库连接器"""
    
    def _create_engine(self) -> Engine:
        return create_engine(
            self.config.db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 10}
        )
    
    def get_schema_info(self) -> str:
        sql = """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        df = self.execute_query(sql)
        
        tables = df.groupby("table_name")
        lines = []
        for table_name, group in tables:
            lines.append(f"-- {table_name}")
            cols = []
            for _, row in group.iterrows():
                nullable = "" if row["is_nullable"] == "YES" else " NOT NULL"
                cols.append(f"  {row['column_name']} {row['data_type']}{nullable}")
            lines.append("CREATE TABLE " + table_name + " (\n" + ",\n".join(cols) + "\n);")
        return "\n\n".join(lines)


def create_database_connector(config: Optional[DatabaseConfig] = None) -> DatabaseConnector:
    """工厂函数：根据配置创建数据库连接器"""
    if config is None:
        settings = get_settings()
        db_url = settings.db_url
        config = DatabaseConfig(
            db_type=_detect_db_type(db_url),
            db_url=db_url,
            max_rows=settings.sql_max_rows,
            query_timeout=settings.sql_query_timeout,
            readonly=settings.readonly_mode
        )
    
    connectors = {
        "sqlite": SQLiteConnector,
        "mysql": MySQLConnector,
        "postgresql": PostgreSQLConnector,
    }
    
    connector_class = connectors.get(config.db_type)
    if not connector_class:
        raise ValueError(f"Unsupported database type: {config.db_type}")
    
    return connector_class(config)


def _detect_db_type(db_url: str) -> str:
    """从 URL 检测数据库类型"""
    if db_url.startswith("sqlite"):
        return "sqlite"
    elif db_url.startswith("mysql") or db_url.startswith("mysql+pymysql"):
        return "mysql"
    elif db_url.startswith("postgresql") or db_url.startswith("postgres"):
        return "postgresql"
    else:
        raise ValueError(f"Cannot detect database type from URL: {db_url[:50]}...")