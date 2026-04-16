"""
MySQL 数据库连接器

特点：
- 支持连接池
- 支持健康检查
- 支持只读账号
- 支持事务管理
"""
from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from app.core.sql.db_abstraction import (
    DatabaseConnector,
    DatabaseConfig,
    DatabaseType,
    HealthStatus
)


logger = logging.getLogger(__name__)


class MySQLConnector(DatabaseConnector):
    """MySQL 数据库连接器"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._validate_config()
        self._pool_status: Dict[str, Any] = {}
    
    def _validate_config(self) -> None:
        """验证配置"""
        if self.config.db_type != DatabaseType.MYSQL:
            raise ValueError(f"MySQLConnector requires db_type=MYSQL, got {self.config.db_type}")
        
        # MySQL 必须有数据库名
        if not self.config.database:
            # 尝试从 URL 提取
            self.config._parse_url_components(self.config.db_url)
    
    def _create_engine(self) -> Engine:
        """创建 MySQL 引擎"""
        # 构建 MySQL 连接 URL
        url = self.config.db_url
        
        # 确保使用 pymysql 驱动
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+pymysql://")
        elif url.startswith("mysql+mysqlconnector://"):
            url = url.replace("mysql+mysqlconnector://", "mysql+pymysql://")
        
        # 连接参数
        connect_args = {
            "connect_timeout": self.config.query_timeout,
            "charset": "utf8mb4",
        }
        
        # 只读模式下的额外设置
        if self.config.readonly:
            # 设置只读提示（需要 MySQL 8.0+ 或只读账号）
            pass
        
        engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=True,  # 连接前检查有效性
            connect_args=connect_args,
            echo=False,  # 设为 True 可打印 SQL
        )
        
        return engine
    
    def _on_connect(self, dbapi_conn) -> None:
        """连接建立时设置 MySQL 特定选项"""
        cursor = dbapi_conn.cursor()
        
        # 设置时区
        cursor.execute("SET time_zone = '+08:00'")
        
        # 设置字符集
        cursor.execute("SET NAMES utf8mb4")
        
        # 只读模式设置
        if self.config.readonly:
            # 注意：真正的只读应该使用只读账号
            # 这里只是设置会话级别的限制提示
            pass
        
        cursor.close()
    
    def _on_checkout(self, dbapi_conn) -> None:
        """连接从池中取出时的检查"""
        # 可以在此添加心跳检测
        pass
    
    def get_schema_info(self) -> str:
        """获取 MySQL 数据库结构信息"""
        if not self.config.database:
            return ""
        
        sql = f"""
        SELECT 
            table_name,
            column_name,
            column_type,
            is_nullable,
            column_key,
            column_default,
            extra
        FROM information_schema.columns
        WHERE table_schema = :db_name
        ORDER BY table_name, ordinal_position;
        """
        
        result = self.execute_query(sql, params={"db_name": self.config.database})
        
        if not result.success or result.data is None:
            return ""
        
        # 按表分组生成 DDL 风格描述
        tables = result.data.groupby("table_name")
        lines = []
        
        for table_name, group in tables:
            lines.append(f"-- {table_name}")
            cols = []
            
            for _, row in group.iterrows():
                nullable = "" if row["is_nullable"] == "YES" else " NOT NULL"
                key = f" {row['column_key']}" if row["column_key"] else ""
                default = f" DEFAULT {row['column_default']}" if row["column_default"] else ""
                extra = f" {row['extra']}" if row["extra"] else ""
                cols.append(f"  {row['column_name']} {row['column_type']}{nullable}{default}{key}{extra}")
            
            lines.append(f"CREATE TABLE {table_name} (\n" + ",\n".join(cols) + "\n);")
        
        return "\n\n".join(lines)
    
    def get_table_names(self) -> List[str]:
        """获取所有表名"""
        if not self.config.database:
            return []
        
        sql = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :db_name
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        
        result = self.execute_query(sql, params={"db_name": self.config.database})
        
        if not result.success or result.data is None:
            return []
        
        return result.data["table_name"].tolist()
    
    def get_column_info(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        if not self.config.database:
            return []
        
        sql = """
        SELECT 
            column_name,
            column_type,
            is_nullable,
            column_key,
            column_default,
            extra,
            column_comment
        FROM information_schema.columns
        WHERE table_schema = :db_name
          AND table_name = :table_name
        ORDER BY ordinal_position;
        """
        
        result = self.execute_query(
            sql, 
            params={"db_name": self.config.database, "table_name": table_name}
        )
        
        if not result.success or result.data is None:
            return []
        
        columns = []
        for _, row in result.data.iterrows():
            columns.append({
                "name": row["column_name"],
                "type": row["column_type"],
                "nullable": row["is_nullable"] == "YES",
                "primary_key": row["column_key"] == "PRI",
                "default": row.get("column_default"),
                "comment": row.get("column_comment"),
            })
        
        return columns
    
    def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """获取表统计信息"""
        stats = {
            "table_name": table_name,
            "row_count": 0,
            "size_bytes": 0,
            "engine": "InnoDB",
        }
        
        try:
            # 获取行数（近似值，对于大表更快）
            sql = """
            SELECT 
                table_rows,
                data_length + index_length as size_bytes,
                engine
            FROM information_schema.tables
            WHERE table_schema = :db_name
              AND table_name = :table_name;
            """
            
            result = self.execute_query(
                sql,
                params={"db_name": self.config.database, "table_name": table_name}
            )
            
            if result.success and result.data is not None and len(result.data) > 0:
                row = result.data.iloc[0]
                stats["row_count"] = int(row["table_rows"])
                stats["size_bytes"] = int(row["size_bytes"])
                stats["engine"] = row["engine"]
        
        except Exception as e:
            logger.warning(f"Failed to get table stats: {e}")
        
        return stats
    
    def get_pool_status(self) -> Dict[str, Any]:
        """获取连接池状态"""
        try:
            pool = self.engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "is_valid": True,
            }
        except Exception as e:
            return {
                "pool_size": 0,
                "checked_in": 0,
                "checked_out": 0,
                "overflow": 0,
                "is_valid": False,
                "error": str(e),
            }
    
    def test_connection(self) -> HealthStatus:
        """测试 MySQL 连接"""
        import time
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                # 执行简单查询
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                
                # 获取版本信息
                version_result = conn.execute(text("SELECT VERSION()"))
                version = version_result.fetchone()[0]
            
            latency = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=True,
                db_type="mysql",
                latency_ms=round(latency, 2),
                message="Connection successful",
                details={
                    "version": version,
                    "database": self.config.database,
                    "host": self.config.host,
                    "pool_status": self.get_pool_status(),
                }
            )
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return HealthStatus(
                is_healthy=False,
                db_type="mysql",
                latency_ms=round(latency, 2),
                message=str(e),
                details={
                    "database": self.config.database,
                    "host": self.config.host,
                }
            )
    
    def begin_transaction(self):
        """开始事务"""
        return self.engine.begin()
    
    def execute_in_transaction(
        self, 
        statements: List[str]
    ) -> Dict[str, Any]:
        """
        在事务中执行多条语句
        
        注意：只读模式下不应该使用此方法
        """
        if self.config.readonly:
            raise RuntimeError("Cannot execute transactions in readonly mode")
        
        results = {
            "success": True,
            "statements_executed": 0,
            "errors": [],
        }
        
        try:
            with self.engine.begin() as conn:
                for stmt in statements:
                    try:
                        conn.execute(text(stmt))
                        results["statements_executed"] += 1
                    except SQLAlchemyError as e:
                        results["errors"].append(str(e))
                        # 事务会自动回滚
                        raise
        except Exception as e:
            results["success"] = False
            results["errors"].append(str(e))
        
        return results