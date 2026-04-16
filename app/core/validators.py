"""
输入验证模块 - Text2SQL 版本

使用 Pydantic 对所有 API 输入进行严格校验。
"""
from __future__ import annotations

from typing import Optional, List
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# 请求模型
# ============================================================================

class AskRequest(BaseModel):
    """自然语言查询请求"""
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="自然语言问题",
    )
    db_name: Optional[str] = Field(
        None,
        max_length=100,
        description="数据库名称",
    )
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """验证问题格式"""
        # 去除首尾空白
        v = v.strip()
        
        # 检查是否为空
        if not v:
            raise ValueError("问题不能为空")
        
        # 检查是否包含明显的 SQL 注入尝试
        dangerous_patterns = [
            "--",  # SQL 注释
            "/*",  # 多行注释开始
            "*/",  # 多行注释结束
            ";",   # 语句分隔符（在问题中不应该出现）
        ]
        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError(f"问题包含不允许的字符: {pattern}")
        
        return v
    
    @field_validator("db_name")
    @classmethod
    def validate_db_name(cls, v: Optional[str]) -> Optional[str]:
        """验证数据库名称"""
        if v is None:
            return v
        
        # 只允许字母、数字、下划线
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("数据库名称只能包含字母、数字和下划线")
        
        return v


class SchemaRequest(BaseModel):
    """Schema 获取请求"""
    db_name: Optional[str] = Field(
        None,
        max_length=100,
        description="数据库名称",
    )
    
    @field_validator("db_name")
    @classmethod
    def validate_db_name(cls, v: Optional[str]) -> Optional[str]:
        """验证数据库名称"""
        if v is None:
            return v
        
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("数据库名称只能包含字母、数字和下划线")
        
        return v


class ExecuteSQLRequest(BaseModel):
    """SQL 执行请求（如果 API 暴露此功能）"""
    sql: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="SQL 查询语句",
    )
    db_name: Optional[str] = Field(
        None,
        max_length=100,
        description="数据库名称",
    )
    max_rows: int = Field(
        100,
        ge=1,
        le=1000,
        description="最大返回行数",
    )
    
    @field_validator("sql")
    @classmethod
    def validate_sql(cls, v: str) -> str:
        """验证 SQL 语句"""
        v = v.strip()
        
        # 只允许 SELECT 语句
        if not v.upper().startswith("SELECT"):
            raise ValueError("只允许执行 SELECT 查询")
        
        # 检查危险操作
        dangerous_keywords = [
            "DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT",
            "ALTER", "CREATE", "GRANT", "REVOKE",
        ]
        sql_upper = v.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError(f"SQL 包含不允许的操作: {keyword}")
        
        return v


# ============================================================================
# 文件上传验证（如果支持）
# ============================================================================

class FileUpload(BaseModel):
    """文件上传验证"""
    filename: str = Field(..., max_length=255)
    content_type: str = Field(..., max_length=100)
    size_bytes: int = Field(..., ge=1)
    
    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """验证文件名"""
        ext = Path(v).suffix.lower()
        allowed_extensions = [".csv", ".xlsx", ".xls", ".sql", ".ddl"]
        if ext not in allowed_extensions:
            raise ValueError(f"不支持的文件格式: {ext}，支持: {', '.join(allowed_extensions)}")
        return v
    
    @field_validator("size_bytes")
    @classmethod
    def validate_size(cls, v: int) -> int:
        """验证文件大小"""
        max_size = 50 * 1024 * 1024  # 50MB
        if v > max_size:
            raise ValueError(f"文件大小超过限制 ({v} > {max_size})")
        return v


# ============================================================================
# 便捷验证函数
# ============================================================================

def validate_question(question: str) -> str:
    """
    验证自然语言问题
    
    Args:
        question: 待验证的问题
        
    Returns:
        str: 验证后的问题
        
    Raises:
        ValueError: 验证失败
    """
    req = AskRequest(question=question)
    return req.question


def validate_sql_safety(sql: str) -> str:
    """
    验证 SQL 安全性
    
    Args:
        sql: 待验证的 SQL
        
    Returns:
        str: 验证后的 SQL
        
    Raises:
        ValueError: 验证失败
    """
    req = ExecuteSQLRequest(sql=sql)
    return req.sql