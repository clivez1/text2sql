"""
权限控制系统

提供表级别的只读权限控制和敏感字段过滤功能。

功能：
1. 表级别权限控制（允许/禁止访问特定表）
2. 列级别权限控制（敏感字段过滤）
3. 行级别权限控制（可选）
4. 权限缓存
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set, List, Dict, Any, Callable
from functools import lru_cache
import re

import pandas as pd


logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """权限级别"""
    DENIED = "denied"          # 禁止访问
    READ_ONLY = "read_only"    # 只读
    READ_WRITE = "read_write"  # 读写（不推荐用于 Text2SQL）
    ADMIN = "admin"            # 管理员权限


@dataclass
class TablePermission:
    """表权限配置"""
    table_name: str
    permission_level: PermissionLevel = PermissionLevel.READ_ONLY
    allowed_columns: Optional[Set[str]] = None      # None 表示允许所有列
    denied_columns: Optional[Set[str]] = None       # 禁止访问的列
    row_filter: Optional[str] = None                # 行级过滤条件（如 "tenant_id = 1"）
    max_rows: Optional[int] = None                  # 最大返回行数
    description: str = ""
    
    def is_column_allowed(self, column_name: str) -> bool:
        """检查列是否允许访问"""
        # 先检查禁止列表
        if self.denied_columns and column_name.lower() in {c.lower() for c in self.denied_columns}:
            return False
        
        # 再检查允许列表
        if self.allowed_columns is None:
            return True
        
        return column_name.lower() in {c.lower() for c in self.allowed_columns}
    
    def get_allowed_columns(self, all_columns: List[str]) -> List[str]:
        """获取允许访问的列"""
        return [col for col in all_columns if self.is_column_allowed(col)]


@dataclass
class UserContext:
    """用户上下文"""
    user_id: str
    roles: Set[str] = field(default_factory=set)
    tenant_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def has_role(self, role: str) -> bool:
        """检查用户是否有指定角色"""
        return role in self.roles


class PermissionManager:
    """
    权限管理器
    
    管理表级别和列级别的访问权限。
    """
    
    # 敏感字段黑名单（默认）
    DEFAULT_SENSITIVE_COLUMNS: Set[str] = {
        "password", "passwd", "pwd", "secret", "token",
        "api_key", "apikey", "private_key", "privatekey",
        "credit_card", "creditcard", "card_number",
        "ssn", "social_security", "id_card",
        "access_token", "refresh_token", "auth_token",
        "salt", "hash", "encrypted", "secret_key",
    }
    
    def __init__(
        self,
        default_permission: PermissionLevel = PermissionLevel.READ_ONLY,
        sensitive_columns: Optional[Set[str]] = None,
        enable_cache: bool = True,
    ):
        """
        初始化权限管理器
        
        Args:
            default_permission: 默认权限级别
            sensitive_columns: 敏感字段集合
            enable_cache: 是否启用权限缓存
        """
        self.default_permission = default_permission
        self.sensitive_columns = sensitive_columns or self.DEFAULT_SENSITIVE_COLUMNS
        self.enable_cache = enable_cache
        
        # 表权限配置
        self._table_permissions: Dict[str, TablePermission] = {}
        
        # 全局表白名单
        self._allowed_tables: Set[str] = set()
        
        # 用户角色权限映射
        self._role_permissions: Dict[str, Set[str]] = {}
    
    def register_table_permission(self, permission: TablePermission) -> None:
        """注册表权限配置"""
        self._table_permissions[permission.table_name.lower()] = permission
        
        # 清除缓存
        if self.enable_cache:
            self._get_table_permission.cache_clear()
    
    def set_allowed_tables(self, tables: Set[str]) -> None:
        """设置允许访问的表（白名单）"""
        self._allowed_tables = {t.lower() for t in tables}
    
    def add_allowed_table(self, table_name: str) -> None:
        """添加允许访问的表"""
        self._allowed_tables.add(table_name.lower())
    
    def set_role_tables(self, role: str, tables: Set[str]) -> None:
        """设置角色可访问的表"""
        self._role_permissions[role] = {t.lower() for t in tables}
    
    @lru_cache(maxsize=256)
    def _get_table_permission(self, table_name: str) -> Optional[TablePermission]:
        """获取表的权限配置（带缓存）"""
        return self._table_permissions.get(table_name.lower())
    
    def check_table_access(
        self,
        table_name: str,
        user_context: Optional[UserContext] = None,
        required_level: PermissionLevel = PermissionLevel.READ_ONLY,
    ) -> bool:
        """
        检查表的访问权限
        
        Args:
            table_name: 表名
            user_context: 用户上下文
            required_level: 需要的权限级别
            
        Returns:
            bool: 是否有权限
        """
        table_name = table_name.lower()
        
        # 1. 检查全局白名单
        if self._allowed_tables and table_name not in self._allowed_tables:
            logger.warning(f"Table '{table_name}' not in allowed list")
            return False
        
        # 2. 检查角色权限
        if user_context:
            for role in user_context.roles:
                role_tables = self._role_permissions.get(role, set())
                if table_name in role_tables:
                    return True
        
        # 3. 检查表级权限配置
        permission = self._get_table_permission(table_name)
        if permission:
            return self._check_permission_level(
                permission.permission_level,
                required_level
            )
        
        # 4. 使用默认权限
        return self._check_permission_level(self.default_permission, required_level)
    
    def _check_permission_level(
        self,
        actual: PermissionLevel,
        required: PermissionLevel
    ) -> bool:
        """检查权限级别是否满足"""
        levels = {
            PermissionLevel.DENIED: 0,
            PermissionLevel.READ_ONLY: 1,
            PermissionLevel.READ_WRITE: 2,
            PermissionLevel.ADMIN: 3,
        }
        return levels.get(actual, 0) >= levels.get(required, 0)
    
    def get_allowed_columns(
        self,
        table_name: str,
        all_columns: List[str],
        user_context: Optional[UserContext] = None,
    ) -> List[str]:
        """
        获取表允许访问的列
        
        Args:
            table_name: 表名
            all_columns: 所有列名
            user_context: 用户上下文
            
        Returns:
            List[str]: 允许访问的列名列表
        """
        table_name = table_name.lower()
        
        # 获取表权限配置
        permission = self._get_table_permission(table_name)
        
        # 过滤敏感字段
        allowed = []
        for col in all_columns:
            col_lower = col.lower()
            
            # 检查敏感字段
            if col_lower in self.sensitive_columns:
                # 管理员可以访问敏感字段
                if user_context and user_context.has_role("admin"):
                    allowed.append(col)
                continue
            
            # 检查表级权限
            if permission and not permission.is_column_allowed(col):
                continue
            
            allowed.append(col)
        
        return allowed
    
    def filter_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        user_context: Optional[UserContext] = None,
    ) -> pd.DataFrame:
        """
        过滤 DataFrame 中的敏感列
        
        Args:
            df: 原始 DataFrame
            table_name: 表名
            user_context: 用户上下文
            
        Returns:
            pd.DataFrame: 过滤后的 DataFrame
        """
        allowed_columns = self.get_allowed_columns(
            table_name,
            list(df.columns),
            user_context
        )
        
        # 只保留允许的列
        return df[allowed_columns]
    
    def get_row_filter(
        self,
        table_name: str,
        user_context: Optional[UserContext] = None,
    ) -> Optional[str]:
        """
        获取行级过滤条件
        
        Args:
            table_name: 表名
            user_context: 用户上下文
            
        Returns:
            Optional[str]: WHERE 条件语句
        """
        table_name = table_name.lower()
        permission = self._get_table_permission(table_name)
        
        if permission and permission.row_filter:
            return permission.row_filter
        
        return None
    
    def get_max_rows(
        self,
        table_name: str,
        default_max: int = 200,
    ) -> int:
        """获取表的最大返回行数"""
        table_name = table_name.lower()
        permission = self._get_table_permission(table_name)
        
        if permission and permission.max_rows:
            return permission.max_rows
        
        return default_max
    
    def validate_sql_tables(
        self,
        sql: str,
        user_context: Optional[UserContext] = None,
    ) -> tuple[bool, List[str]]:
        """
        验证 SQL 中的表是否都有权限访问
        
        Args:
            sql: SQL 语句
            user_context: 用户上下文
            
        Returns:
            tuple[bool, List[str]]: (是否全部有权限, 无权限的表列表)
        """
        # 提取表名
        tables = self._extract_tables_from_sql(sql)
        
        denied_tables = []
        for table in tables:
            if not self.check_table_access(table, user_context):
                denied_tables.append(table)
        
        return len(denied_tables) == 0, denied_tables
    
    def _extract_tables_from_sql(self, sql: str) -> Set[str]:
        """从 SQL 中提取表名"""
        pattern = re.compile(
            r"\b(?:from|join)\s+([a-zA-Z_][\w]*)",
            re.IGNORECASE
        )
        return {match.group(1).lower() for match in pattern.finditer(sql)}


# 默认权限管理器
_default_manager: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """获取权限管理器实例"""
    global _default_manager
    if _default_manager is None:
        _default_manager = PermissionManager()
    return _default_manager


def check_table_access(
    table_name: str,
    user_context: Optional[UserContext] = None,
) -> bool:
    """检查表访问权限（便捷函数）"""
    return get_permission_manager().check_table_access(table_name, user_context)


def filter_sensitive_columns(
    df: pd.DataFrame,
    table_name: str,
    user_context: Optional[UserContext] = None,
) -> pd.DataFrame:
    """过滤敏感列（便捷函数）"""
    return get_permission_manager().filter_dataframe(df, table_name, user_context)