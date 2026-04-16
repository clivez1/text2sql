"""
SQL 执行器
使用 db_abstraction 层执行查询
"""
from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from app.core.sql.db_abstraction import (
    create_connector,
    DatabaseConnector,
    DatabaseConfig,
    QueryResult,
)
from app.core.sql.guard import validate_readonly_sql, SQLValidator, get_validator
from app.core.auth.permission import get_permission_manager
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def _create_db_config() -> DatabaseConfig:
    """从 settings 创建 DatabaseConfig"""
    settings = get_settings()
    return DatabaseConfig.from_url(
        settings.db_url,
        max_rows=settings.sql_max_rows,
        query_timeout=settings.sql_query_timeout,
    )


class QueryExecutor:
    """查询执行器"""
    
    def __init__(
        self,
        db_connector: Optional[DatabaseConnector] = None,
        validator: Optional[SQLValidator] = None
    ):
        self._db = db_connector
        self._validator = validator
    
    @property
    def db(self) -> DatabaseConnector:
        if self._db is None:
            self._db = create_connector(_create_db_config())
        return self._db
    
    @property
    def validator(self) -> SQLValidator:
        if self._validator is None:
            self._validator = get_validator()
        return self._validator
    
    def execute(self, sql: str, validate: bool = True) -> pd.DataFrame:
        """
        执行 SQL 查询
        
        Args:
            sql: SQL 语句
            validate: 是否进行安全校验
            
        Returns:
            查询结果 DataFrame
        """
        if validate:
            safe_sql = validate_readonly_sql(sql)
        else:
            safe_sql = sql
        
        # 表级权限检查
        permission_manager = get_permission_manager()
        has_access, denied_tables = permission_manager.validate_sql_tables(safe_sql)
        if not has_access:
            raise PermissionError(f"Access denied to tables: {denied_tables}")
        
        logger.debug(f"Executing SQL: {safe_sql[:100]}...")
        
        try:
            result: QueryResult = self.db.execute_query(safe_sql)
            if not result.success:
                raise RuntimeError(result.error or "Query execution failed")
            df = result.data
            logger.info(f"Query returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def test_connection(self) -> tuple[bool, str]:
        """测试数据库连接"""
        status = self.db.test_connection()
        return status.is_healthy, status.message
    
    def get_schema_info(self) -> str:
        """获取数据库结构信息"""
        return self.db.get_schema_info()


# 默认执行器实例
_default_executor: Optional[QueryExecutor] = None


def get_executor() -> QueryExecutor:
    """获取查询执行器"""
    global _default_executor
    if _default_executor is None:
        _default_executor = QueryExecutor()
    return _default_executor


def run_query(sql: str) -> pd.DataFrame:
    """
    执行查询（向后兼容接口）
    
    Args:
        sql: SQL 语句
        
    Returns:
        查询结果 DataFrame
    """
    return get_executor().execute(sql)
