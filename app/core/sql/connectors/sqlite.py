"""
SQLite 数据库连接器

特点：
- 支持只读模式
- 轻量级，适合 Demo 和开发环境
- 支持 URI 连接方式
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine

from app.core.sql.db_abstraction import (
    DatabaseConnector,
    DatabaseConfig,
    DatabaseType
)


class SQLiteConnector(DatabaseConnector):
    """SQLite 数据库连接器"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._validate_config()
    
    def _validate_config(self) -> None:
        """验证配置"""
        if self.config.db_type != DatabaseType.SQLITE:
            raise ValueError(f"SQLiteConnector requires db_type=SQLITE, got {self.config.db_type}")
    
    def _create_engine(self) -> Engine:
        """创建 SQLite 引擎"""
        url = self.config.db_url
        
        # 只读模式处理
        if self.config.readonly:
            if url.startswith("sqlite:///"):
                # 转换为 URI 格式以支持只读模式
                # sqlite:///path/to/db.db -> sqlite:///file:path/to/db.db?mode=ro&uri=true
                db_path = url[len("sqlite:///"):]
                url = f"sqlite:///file:{db_path}?mode=ro&uri=true"
            elif "mode=" not in url:
                # 如果没有指定模式，添加只读
                url = url.rstrip("/") + "?mode=ro"
        
        engine = create_engine(
            url,
            pool_pre_ping=True,
            # SQLite 不需要连接池
            poolclass=None
        )
        
        return engine
    
    def _on_connect(self, dbapi_conn) -> None:
        """连接建立时设置 SQLite 特定选项"""
        # 启用外键约束
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    def get_schema_info(self) -> str:
        """获取 SQLite 数据库结构信息"""
        sql = """
        SELECT name, sql 
        FROM sqlite_master 
        WHERE type='table' 
          AND name NOT LIKE 'sqlite_%'
          AND name NOT LIKE 'chroma_%'
        ORDER BY name;
        """
        result = self.execute_query(sql)
        
        if not result.success or result.data is None:
            return ""
        
        return "\n\n".join(
            f"-- {row['name']}\n{row['sql']}"
            for _, row in result.data.iterrows()
        )
    
    def get_table_names(self) -> List[str]:
        """获取所有表名"""
        sql = """
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' 
          AND name NOT LIKE 'sqlite_%'
          AND name NOT LIKE 'chroma_%'
        ORDER BY name;
        """
        result = self.execute_query(sql)
        
        if not result.success or result.data is None:
            return []
        
        return result.data["name"].tolist()
    
    def get_column_info(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        # SQLite 使用 PRAGMA 获取列信息
        sql = f"PRAGMA table_info({table_name});"
        result = self.execute_query(sql)
        
        if not result.success or result.data is None:
            return []
        
        columns = []
        for _, row in result.data.iterrows():
            columns.append({
                "name": row["name"],
                "type": row["type"],
                "nullable": row["notnull"] == 0,
                "primary_key": row["pk"] == 1,
                "default": row.get("dflt_value"),
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
            # 获取行数
            result = self.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
            if result.success and result.data is not None:
                stats["row_count"] = int(result.data.iloc[0]["cnt"])
        except Exception:
            pass
        
        return stats