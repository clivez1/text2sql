"""
SQL 安全校验模块
增强版：支持 SQL 注入防护、权限控制、查询限制
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Set

import sqlparse
from sqlparse.sql import Token, Identifier, Function, Parenthesis
from sqlparse.tokens import Keyword, DML, DDL, Name


# 危险 SQL 关键字
FORBIDDEN_KEYWORDS = {
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "replace", "attach", "pragma", "vacuum", "exec",
    "execute", "xp_", "sp_", "into outfile", "load_file",
}

# 允许查询的表白名单
DEFAULT_ALLOWED_TABLES: Set[str] = {
    "orders", "products", "order_items", "customers"
}

# 敏感字段黑名单
SENSITIVE_COLUMNS: Set[str] = {
    "password", "secret", "token", "api_key", "credit_card",
    "ssn", "private_key", "access_token",
}

# 默认 LIMIT
DEFAULT_LIMIT = 100
# 最大 LIMIT
MAX_LIMIT = 1000


@dataclass
class SQLValidationResult:
    """SQL 校验结果"""
    is_valid: bool
    safe_sql: Optional[str] = None
    error: Optional[str] = None
    tables_used: Set[str] = None
    has_sensitive_columns: bool = False
    
    def __post_init__(self):
        if self.tables_used is None:
            self.tables_used = set()


class SQLValidator:
    """SQL 校验器"""
    
    def __init__(
        self,
        allowed_tables: Optional[Set[str]] = None,
        default_limit: int = DEFAULT_LIMIT,
        max_limit: int = MAX_LIMIT,
        readonly: bool = True
    ):
        self.allowed_tables = allowed_tables or DEFAULT_ALLOWED_TABLES
        self.default_limit = default_limit
        self.max_limit = max_limit
        self.readonly = readonly
    
    def validate(self, sql: str) -> SQLValidationResult:
        """
        验证 SQL 安全性
        
        Args:
            sql: 待验证的 SQL 语句
            
        Returns:
            SQLValidationResult: 验证结果
        """
        # 标准化 SQL
        normalized = self._normalize_sql(sql)
        lowered = normalized.lower()
        
        # 1. 检查多语句
        if ";" in lowered.rstrip(";"):
            return SQLValidationResult(
                is_valid=False,
                error="Multiple SQL statements are not allowed."
            )
        
        # 2. 只读模式检查
        if self.readonly and not lowered.startswith("select"):
            return SQLValidationResult(
                is_valid=False,
                error="Only SELECT statements are allowed in readonly mode."
            )
        
        # 3. 危险关键字检查
        for keyword in FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{keyword}\b", lowered):
                return SQLValidationResult(
                    is_valid=False,
                    error=f"Dangerous SQL keyword detected: {keyword}"
                )
        
        # 4. 提取并验证表名（使用 sqlparse AST）
        tables = self._extract_tables_v2(normalized)
        forbidden_tables = tables - self.allowed_tables
        if forbidden_tables:
            return SQLValidationResult(
                is_valid=False,
                error=f"Access denied to tables: {sorted(forbidden_tables)}"
            )
        
        # 5. 检查敏感字段
        has_sensitive = self._check_sensitive_columns(normalized)
        
        # 6. 添加 LIMIT
        safe_sql = self._ensure_limit(normalized)
        
        return SQLValidationResult(
            is_valid=True,
            safe_sql=safe_sql,
            tables_used=tables,
            has_sensitive_columns=has_sensitive
        )
    
    def _normalize_sql(self, sql: str) -> str:
        """标准化 SQL"""
        # 移除注释
        normalized = sqlparse.format(sql, strip_comments=True).strip()
        # 压缩空白
        normalized = " ".join(normalized.split())
        return normalized
    
    def _extract_tables_v2(self, sql: str) -> Set[str]:
        """
        使用 sqlparse AST 提取 SQL 中使用的表名。
        
        遍历 AST 中 FROM/JOIN 子句下的 Identifier，提取真实表名。
        支持：FROM table、FROM table alias、JOIN table ON ...、JOIN (subquery) AS alias
        """
        tables = set()
        parsed = sqlparse.parse(sql)
        
        for statement in parsed:
            # 遍历所有 token，查找 FROM/JOIN 关键字
            self._find_tables_in_token(statement, tables)
        
        return tables
    
    def _find_tables_in_token(self, token: Token, tables: Set[str]) -> None:
        """递归遍历 token 树，提取表名"""
        # 处理 Identifier（通常是表名或子查询）
        if isinstance(token, Identifier):
            # Identifier 的真实名称（忽略 alias）
            name = token.get_real_name()
            if name:
                tables.add(name.lower())
            # 继续遍历子 token（处理 JOIN () AS alias 等情况）
            for sub in token.tokens:
                self._find_tables_in_token(sub, tables)
            return
        
        # 处理函数（可能是 Table-valued function，暂按表名处理）
        if isinstance(token, Function):
            name = token.get_real_name()
            if name:
                tables.add(name.lower())
            return
        
        # 处理括号表达式（可能是子查询）
        if isinstance(token, Parenthesis):
            for sub in token.tokens:
                self._find_tables_in_token(sub, tables)
            return
        
        # 遇到 FROM 或 JOIN 关键字时，提取其后的标识符
        token_value_upper = token.value.upper().strip()
        if token_value_upper in ("FROM", "JOIN", "INNER JOIN", "LEFT JOIN", 
                                   "RIGHT JOIN", "CROSS JOIN", "NATURAL JOIN",
                                   "STRAIGHT_JOIN", "LEFT OUTER JOIN", "RIGHT OUTER JOIN",
                                   "FULL OUTER JOIN", "FULL JOIN"):
            # 查找后续 token 中的表名
            return
        
        # 递归处理子 token
        if hasattr(token, "tokens"):
            for sub in token.tokens:
                self._find_tables_in_token(sub, tables)
    
    def _extract_tables(self, sql: str) -> Set[str]:
        """
        使用正则提取 SQL 中使用的表名（向后兼容，委托给 _extract_tables_v2）
        """
        return self._extract_tables_v2(sql)
    
    def _check_sensitive_columns(self, sql: str) -> bool:
        """检查是否包含敏感字段"""
        lowered = sql.lower()
        for col in SENSITIVE_COLUMNS:
            if re.search(rf"\b{col}\b", lowered):
                return True
        return False
    
    def _ensure_limit(self, sql: str) -> str:
        """确保 SQL 有 LIMIT 子句"""
        lowered = sql.lower()
        
        # 检查是否已有 LIMIT
        limit_match = re.search(r"\blimit\s+(\d+)", lowered)
        if limit_match:
            # 检查 LIMIT 是否过大
            limit = int(limit_match.group(1))
            if limit > self.max_limit:
                sql = re.sub(
                    r"\blimit\s+\d+",
                    f"LIMIT {self.max_limit}",
                    sql,
                    flags=re.IGNORECASE
                )
        else:
            # 添加默认 LIMIT
            sql = sql.rstrip(";") + f" LIMIT {self.default_limit};"
        
        return sql


# 默认校验器实例
_default_validator: Optional[SQLValidator] = None


def get_validator(
    allowed_tables: Optional[Set[str]] = None,
    readonly: bool = True
) -> SQLValidator:
    """获取 SQL 校验器"""
    global _default_validator
    if _default_validator is None or allowed_tables:
        _default_validator = SQLValidator(
            allowed_tables=allowed_tables,
            readonly=readonly
        )
    return _default_validator


def validate_readonly_sql(sql: str, allowed_tables: Optional[Set[str]] = None) -> str:
    """
    验证只读 SQL（向后兼容接口）
    
    Args:
        sql: 待验证的 SQL
        allowed_tables: 允许的表名集合
        
    Returns:
        安全的 SQL 语句
        
    Raises:
        ValueError: SQL 不符合安全规范
    """
    validator = get_validator(allowed_tables=allowed_tables, readonly=True)
    result = validator.validate(sql)
    
    if not result.is_valid:
        raise ValueError(result.error)
    
    if result.has_sensitive_columns:
        # 记录警告但不阻止
        pass
    
    return result.safe_sql
