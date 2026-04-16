"""
PostgreSQL 数据库连接器

特点：
- 支持连接池
- 支持健康检查
- 支持只读事务
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from app.core.sql.db_abstraction import (
    DatabaseConnector,
    DatabaseConfig,
    DatabaseType,
    HealthStatus
)


logger = logging.getLogger(__name__)


class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL 数据库连接器"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._validate_config()
    
    def _validate_config(self) -> None:
        """验证配置"""
        if self.config.db_type != DatabaseType.POSTGRESQL:
            raise ValueError(
                f"PostgreSQLConnector requires db_type=POSTGRESQL, got {self.config.db_type}"
            )
        
        if not self.config.database:
            self.config._parse_url_components(self.config.db_url)
    
    def _create_engine(self) -> Engine:
        """创建 PostgreSQL 引擎"""
        url = self.config.db_url
        
        # 确保使用 psycopg2 驱动
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://")
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://")
        
        connect_args = {
            "connect_timeout": self.config.query_timeout,
        }
        
        # 只读模式设置
        if self.config.readonly:
            connect_args["options"] = "-c default_transaction_read_only=on"
        
        engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        
        return engine
    
    def _on_connect(self, dbapi_conn) -> None:
        """连接建立时设置 PostgreSQL 特定选项"""
        cursor = dbapi_conn.cursor()
        
        # 设置时区
        cursor.execute("SET TIME ZONE 'Asia/Shanghai'")
        
        cursor.close()
    
    def get_schema_info(self) -> str:
        """获取 PostgreSQL 数据库结构信息"""
        sql = """
        SELECT 
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        
        result = self.execute_query(sql)
        
        if not result.success or result.data is None:
            return ""
        
        tables = result.data.groupby("table_name")
        lines = []
        
        for table_name, group in tables:
            lines.append(f"-- {table_name}")
            cols = []
            
            for _, row in group.iterrows():
                nullable = "" if row["is_nullable"] == "YES" else " NOT NULL"
                dtype = row["data_type"]
                if row.get("character_maximum_length"):
                    dtype = f"varchar({row['character_maximum_length']})"
                default = f" DEFAULT {row['column_default']}" if row.get("column_default") else ""
                cols.append(f"  {row['column_name']} {dtype}{nullable}{default}")
            
            lines.append(f"CREATE TABLE {table_name} (\n" + ",\n".join(cols) + "\n);")
        
        return "\n\n".join(lines)
    
    def get_table_names(self) -> List[str]:
        """获取所有表名"""
        sql = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        result = self.execute_query(sql)
        
        if not result.success or result.data is None:
            return []
        
        return result.data["table_name"].tolist()
    
    def get_column_info(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        sql = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :table_name
        ORDER BY ordinal_position;
        """
        
        result = self.execute_query(sql, params={"table_name": table_name})
        
        if not result.success or result.data is None:
            return []
        
        columns = []
        for _, row in result.data.iterrows():
            columns.append({
                "name": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES",
                "primary_key": False,  # 需要额外查询
                "default": row.get("column_default"),
            })
        
        return columns
    
    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """获取表统计信息"""
        stats = {
            "table_name": table_name,
            "row_count": 0,
            "size_bytes": 0,
        }
        
        try:
            # PostgreSQL 使用 pg_stat_user_tables
            sql = """
            SELECT 
                n_live_tup as row_count,
                pg_total_relation_size(schemaname || '.' || tablename) as size_bytes
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
              AND relname = :table_name;
            """
            
            result = self.execute_query(sql, params={"table_name": table_name})
            
            if result.success and result.data is not None and len(result.data) > 0:
                row = result.data.iloc[0]
                stats["row_count"] = int(row["row_count"] or 0)
                stats["size_bytes"] = int(row["size_bytes"] or 0)
        
        except Exception as e:
            logger.warning(f"Failed to get table stats: {e}")
        
        return stats
    
    def test_connection(self) -> HealthStatus:
        """测试 PostgreSQL 连接"""
        import time
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                
                version_result = conn.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
            
            latency = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=True,
                db_type="postgresql",
                latency_ms=round(latency, 2),
                message="Connection successful",
                details={
                    "version": version,
                    "database": self.config.database,
                }
            )
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=False,
                db_type="postgresql",
                latency_ms=round(latency, 2),
                message=str(e),
            )