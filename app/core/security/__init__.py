"""
安全模块

提供 SQL 注入防护、权限控制等安全功能。
"""
from app.core.security.sql_sanitizer import (
    SQLSanitizer,
    SanitizationResult,
    sanitize_sql,
    is_safe_sql,
)

__all__ = [
    "SQLSanitizer",
    "SanitizationResult",
    "sanitize_sql",
    "is_safe_sql",
]