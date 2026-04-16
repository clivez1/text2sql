"""
SQL 注入防护模块

提供全面的 SQL 安全检查和净化功能。

功能：
1. 危险关键字拦截（INSERT/UPDATE/DELETE/DROP/ALTER/CREATE）
2. SQL 注入模式检测
3. 强制 LIMIT 上限
4. 多语句检测
5. 表名白名单验证
6. 敏感字段过滤
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Optional, Set, List, Tuple
from enum import Enum

import sqlparse
from sqlparse.sql import Statement, Token
from sqlparse.tokens import Keyword, DML, DDL


logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """威胁等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SQLInjectionType(Enum):
    """SQL 注入类型"""
    NONE = "none"
    DANGEROUS_KEYWORD = "dangerous_keyword"
    MULTIPLE_STATEMENTS = "multiple_statements"
    COMMENT_INJECTION = "comment_injection"
    UNION_INJECTION = "union_injection"
    BOOLEAN_BASED = "boolean_based"
    TIME_BASED = "time_based"
    ERROR_BASED = "error_based"


# 危险 SQL 关键字（完整版）
FORBIDDEN_KEYWORDS: Set[str] = {
    # DDL 操作
    "create", "alter", "drop", "truncate", "rename",
    # DML 写操作
    "insert", "update", "delete", "replace", "merge",
    # DCL 操作
    "grant", "revoke",
    # 危险函数和命令
    "exec", "execute", "xp_", "sp_", "shutdown",
    "load_file", "into outfile", "into dumpfile",
    "benchmark", "sleep", "waitfor", "delay",
    # 文件操作
    "load data", "infile",
    # 系统操作
    "pragma", "attach", "detach", "vacuum",
}

# UNION 注入模式
UNION_PATTERNS = [
    r"\bunion\b\s+\bselect\b",
    r"\bunion\b\s+\ball\b\s+\bselect\b",
]

# 注释注入模式
COMMENT_PATTERNS = [
    r"--\s*$",           # SQL 行尾注释
    r"#\s*$",            # MySQL 注释
    r"/\*.*\*/",         # 块注释
    r"/\*!",             # MySQL 特殊注释
]

# 时间盲注模式
TIME_BASED_PATTERNS = [
    r"\bsleep\s*\(",
    r"\bbenchmark\s*\(",
    r"\bwaitfor\b",
    r"\bdelay\b.*\btime\b",
    r"pg_sleep\s*\(",
]

# 布尔盲注模式
BOOLEAN_BASED_PATTERNS = [
    r"\bor\b\s+\d+\s*=\s*\d+",      # OR 1=1
    r"\band\b\s+\d+\s*=\s*\d+",     # AND 1=1
    r"\bor\b\s+'[^']*'\s*=\s*'",    # OR 'a'='a'
    r"\bor\b\s+true\b",
    r"\bor\b\s+1\b",
]

# 敏感字段黑名单
SENSITIVE_COLUMNS: Set[str] = {
    "password", "passwd", "pwd", "secret", "token",
    "api_key", "apikey", "private_key", "privatekey",
    "credit_card", "creditcard", "card_number",
    "ssn", "social_security", "id_card",
    "access_token", "refresh_token", "auth_token",
    "salt", "hash", "encrypted",
}

# 默认允许查询的表白名单
DEFAULT_ALLOWED_TABLES: Set[str] = {
    "orders", "products", "order_items", "customers",
    "users", "categories", "inventory", "sales",
}

# 默认配置
DEFAULT_MAX_LIMIT = 1000
DEFAULT_QUERY_TIMEOUT = 15


@dataclass
class SanitizationResult:
    """SQL 净化结果"""
    original_sql: str
    is_safe: bool = False
    safe_sql: Optional[str] = None
    threat_level: ThreatLevel = ThreatLevel.SAFE
    injection_type: SQLInjectionType = SQLInjectionType.NONE
    detected_threats: List[str] = field(default_factory=list)
    tables_used: Set[str] = field(default_factory=set)
    has_sensitive_columns: bool = False
    limit_applied: bool = False
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "is_safe": self.is_safe,
            "original_sql": self.original_sql,
            "safe_sql": self.safe_sql,
            "threat_level": self.threat_level.value,
            "injection_type": self.injection_type.value,
            "detected_threats": self.detected_threats,
            "tables_used": list(self.tables_used),
            "has_sensitive_columns": self.has_sensitive_columns,
            "limit_applied": self.limit_applied,
            "error_message": self.error_message,
        }


class SQLSanitizer:
    """SQL 安全净化器"""
    
    def __init__(
        self,
        allowed_tables: Optional[Set[str]] = None,
        max_limit: int = DEFAULT_MAX_LIMIT,
        default_limit: int = 100,
        readonly_mode: bool = True,
        strict_mode: bool = True,
    ):
        """
        初始化 SQL 净化器
        
        Args:
            allowed_tables: 允许查询的表名白名单
            max_limit: 最大 LIMIT 值
            default_limit: 默认 LIMIT 值
            readonly_mode: 是否只读模式
            strict_mode: 是否严格模式（检测更多潜在威胁）
        """
        self.allowed_tables = allowed_tables or DEFAULT_ALLOWED_TABLES
        self.max_limit = max_limit
        self.default_limit = default_limit
        self.readonly_mode = readonly_mode
        self.strict_mode = strict_mode
        
        # 编译正则表达式
        self._union_patterns = [re.compile(p, re.IGNORECASE) for p in UNION_PATTERNS]
        self._comment_patterns = [re.compile(p, re.IGNORECASE) for p in COMMENT_PATTERNS]
        self._time_patterns = [re.compile(p, re.IGNORECASE) for p in TIME_BASED_PATTERNS]
        self._boolean_patterns = [re.compile(p, re.IGNORECASE) for p in BOOLEAN_BASED_PATTERNS]
        self._table_pattern = re.compile(
            r"\b(?:from|join)\s+([a-zA-Z_][\w]*)",
            re.IGNORECASE
        )
    
    def sanitize(self, sql: str) -> SanitizationResult:
        """
        净化 SQL 语句
        
        Args:
            sql: 待净化的 SQL 语句
            
        Returns:
            SanitizationResult: 净化结果
        """
        result = SanitizationResult(original_sql=sql)
        
        # 1. 标准化 SQL
        normalized = self._normalize_sql(sql)
        lowered = normalized.lower()
        
        # 2. 检查多语句
        if self._has_multiple_statements(normalized):
            result.is_safe = False
            result.threat_level = ThreatLevel.HIGH
            result.injection_type = SQLInjectionType.MULTIPLE_STATEMENTS
            result.detected_threats.append("Multiple SQL statements detected")
            result.error_message = "Multiple SQL statements are not allowed"
            return result
        
        # 3. 只读模式检查
        if self.readonly_mode:
            if not self._is_readonly_query(normalized):
                result.is_safe = False
                result.threat_level = ThreatLevel.HIGH
                result.injection_type = SQLInjectionType.DANGEROUS_KEYWORD
                result.detected_threats.append("Non-SELECT statement in readonly mode")
                result.error_message = "Only SELECT statements are allowed in readonly mode"
                return result
        
        # 4. 危险关键字检查
        keyword_threat = self._check_dangerous_keywords(lowered)
        if keyword_threat:
            result.is_safe = False
            result.threat_level = ThreatLevel.CRITICAL
            result.injection_type = SQLInjectionType.DANGEROUS_KEYWORD
            result.detected_threats.append(f"Dangerous keyword: {keyword_threat}")
            result.error_message = f"Dangerous SQL operation detected: {keyword_threat}"
            return result
        
        # 5. 注入模式检测
        injection_threats = self._detect_injection_patterns(normalized, lowered)
        if injection_threats:
            result.detected_threats.extend(injection_threats)
            
            # 根据威胁类型设置等级
            for threat in injection_threats:
                if "time" in threat.lower():
                    result.threat_level = ThreatLevel.HIGH
                    result.injection_type = SQLInjectionType.TIME_BASED
                elif "union" in threat.lower():
                    result.threat_level = ThreatLevel.HIGH
                    result.injection_type = SQLInjectionType.UNION_INJECTION
                elif "comment" in threat.lower():
                    result.threat_level = ThreatLevel.MEDIUM
                    result.injection_type = SQLInjectionType.COMMENT_INJECTION
                elif "boolean" in threat.lower():
                    result.threat_level = ThreatLevel.MEDIUM
                    result.injection_type = SQLInjectionType.BOOLEAN_BASED
            
            if self.strict_mode:
                result.is_safe = False
                result.error_message = f"Potential SQL injection detected: {', '.join(injection_threats)}"
                return result
        
        # 6. 提取并验证表名
        tables = self._extract_tables(normalized)
        result.tables_used = tables
        
        forbidden_tables = tables - self.allowed_tables
        if forbidden_tables:
            result.is_safe = False
            result.threat_level = ThreatLevel.HIGH
            result.detected_threats.append(f"Access denied to tables: {sorted(forbidden_tables)}")
            result.error_message = f"Access denied to tables: {', '.join(sorted(forbidden_tables))}"
            return result
        
        # 7. 检查敏感字段
        if self._has_sensitive_columns(normalized):
            result.has_sensitive_columns = True
            result.detected_threats.append("Sensitive columns detected (warning only)")
            logger.warning(f"Sensitive columns detected in query: {sql[:100]}...")
        
        # 8. 添加/调整 LIMIT
        safe_sql = self._ensure_limit(normalized)
        if safe_sql != normalized:
            result.limit_applied = True
        
        # 9. 所有检查通过
        result.is_safe = True
        result.safe_sql = safe_sql
        result.threat_level = ThreatLevel.SAFE if not result.detected_threats else ThreatLevel.LOW
        
        return result
    
    def _normalize_sql(self, sql: str) -> str:
        """标准化 SQL"""
        # 移除注释
        normalized = sqlparse.format(sql, strip_comments=True).strip()
        # 压缩空白
        normalized = " ".join(normalized.split())
        return normalized
    
    def _has_multiple_statements(self, sql: str) -> bool:
        """检查是否有多条语句"""
        parsed = sqlparse.parse(sql)
        return len(parsed) > 1
    
    def _is_readonly_query(self, sql: str) -> bool:
        """检查是否为只读查询"""
        lowered = sql.lower().strip()
        return lowered.startswith("select") or lowered.startswith("with")
    
    def _check_dangerous_keywords(self, lowered_sql: str) -> Optional[str]:
        """检查危险关键字"""
        for keyword in FORBIDDEN_KEYWORDS:
            # 使用单词边界匹配
            if re.search(rf"\b{keyword}\b", lowered_sql):
                return keyword
        return None
    
    def _detect_injection_patterns(self, sql: str, lowered: str) -> List[str]:
        """检测注入模式"""
        threats = []
        
        # UNION 注入
        for pattern in self._union_patterns:
            if pattern.search(sql):
                threats.append("UNION injection pattern detected")
                break
        
        # 注释注入
        for pattern in self._comment_patterns:
            if pattern.search(sql):
                threats.append("Comment-based injection pattern detected")
                break
        
        # 时间盲注
        for pattern in self._time_patterns:
            if pattern.search(sql):
                threats.append("Time-based injection pattern detected")
                break
        
        # 布尔盲注
        if self.strict_mode:
            for pattern in self._boolean_patterns:
                if pattern.search(sql):
                    threats.append("Boolean-based injection pattern detected")
                    break
        
        return threats
    
    def _extract_tables(self, sql: str) -> Set[str]:
        """提取 SQL 中使用的表名"""
        tables = set()
        for match in self._table_pattern.finditer(sql):
            tables.add(match.group(1).lower())
        return tables
    
    def _has_sensitive_columns(self, sql: str) -> bool:
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


# 默认净化器实例
_default_sanitizer: Optional[SQLSanitizer] = None


def get_sanitizer(
    allowed_tables: Optional[Set[str]] = None,
    readonly: bool = True,
    strict: bool = True,
) -> SQLSanitizer:
    """获取 SQL 净化器"""
    global _default_sanitizer
    if _default_sanitizer is None or allowed_tables is not None:
        _default_sanitizer = SQLSanitizer(
            allowed_tables=allowed_tables,
            readonly_mode=readonly,
            strict_mode=strict,
        )
    return _default_sanitizer


def sanitize_sql(
    sql: str,
    allowed_tables: Optional[Set[str]] = None,
    readonly: bool = True,
) -> SanitizationResult:
    """
    净化 SQL 语句（便捷函数）
    
    Args:
        sql: 待净化的 SQL
        allowed_tables: 允许的表名集合
        readonly: 是否只读模式
        
    Returns:
        SanitizationResult: 净化结果
    """
    sanitizer = get_sanitizer(allowed_tables=allowed_tables, readonly=readonly)
    return sanitizer.sanitize(sql)


def is_safe_sql(
    sql: str,
    allowed_tables: Optional[Set[str]] = None,
) -> bool:
    """
    检查 SQL 是否安全
    
    Args:
        sql: 待检查的 SQL
        allowed_tables: 允许的表名集合
        
    Returns:
        bool: 是否安全
    """
    result = sanitize_sql(sql, allowed_tables)
    return result.is_safe