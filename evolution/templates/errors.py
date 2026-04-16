"""
统一错误处理模块 - Text2SQL 版本

适配 Text2SQL Agent 的错误码定义，复用 Data Viz 的架构模式。
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class ErrorCode(Enum):
    """错误码枚举
    
    命名规范: {类别}_{具体错误}
    - 1xxx: 业务错误（客户端输入问题）
    - 2xxx: 安全错误（SQL 安全相关）
    - 3xxx: 系统错误（服务端问题）
    """
    # 业务错误 (1xxx)
    INVALID_QUESTION = 1001
    SQL_GENERATION_ERROR = 1002
    SQL_EXECUTION_ERROR = 1003
    LLM_ERROR = 1004
    VALIDATION_ERROR = 1005
    SCHEMA_NOT_FOUND = 1006
    CHART_RECOMMENDATION_ERROR = 1007
    
    # 安全错误 (2xxx)
    SQL_INJECTION_DETECTED = 2001
    TABLE_NOT_ALLOWED = 2002
    READONLY_VIOLATION = 2003
    UNAUTHORIZED_ACCESS = 2004
    
    # 系统错误 (3xxx)
    INTERNAL_ERROR = 3001
    SERVICE_UNAVAILABLE = 3002
    RATE_LIMITED = 3003
    TIMEOUT = 3004
    DATABASE_ERROR = 3005


@dataclass
class AppError(Exception):
    """统一应用异常
    
    所有业务异常应继承此类，确保错误响应格式统一。
    
    Attributes:
        code: 错误码（ErrorCode 枚举）
        message: 用户友好的错误信息
        detail: 详细错误信息（可选，仅对特定错误暴露给用户）
        context: 错误上下文（用于日志，不暴露给用户）
    """
    code: ErrorCode
    message: str
    detail: Optional[str] = None
    context: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        super().__init__(self.message)
    
    def to_response(self) -> Dict[str, Any]:
        """转换为 API 响应格式"""
        response = {
            "success": False,
            "error": {
                "code": self.code.value,
                "message": self.message,
            }
        }
        
        # 仅对业务错误和安全错误暴露 detail
        if self.detail and self.code.value < 3000:
            response["error"]["detail"] = self.detail
        
        return response
    
    def to_log_dict(self) -> Dict[str, Any]:
        """转换为日志字典"""
        return {
            "error_code": self.code.value,
            "error_name": self.code.name,
            "message": self.message,
            "detail": self.detail,
            "context": self.context,
        }


# ============================================================================
# 具体异常类
# ============================================================================

class ValidationError(AppError):
    """输入验证错误"""
    def __init__(self, message: str = "输入验证失败", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.VALIDATION_ERROR, message=message, detail=detail)


class InvalidQuestionError(AppError):
    """无效问题错误"""
    def __init__(self, message: str = "问题格式无效", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.INVALID_QUESTION, message=message, detail=detail)


class SQLGenerationError(AppError):
    """SQL 生成错误"""
    def __init__(self, message: str = "SQL 生成失败", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.SQL_GENERATION_ERROR, message=message, detail=detail)


class SQLExecutionError(AppError):
    """SQL 执行错误"""
    def __init__(self, message: str = "SQL 执行失败", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.SQL_EXECUTION_ERROR, message=message, detail=detail)


class LLMError(AppError):
    """LLM 调用错误"""
    def __init__(self, message: str = "LLM 服务调用失败", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.LLM_ERROR, message=message, detail=detail)


class SchemaNotFoundError(AppError):
    """Schema 未找到错误"""
    def __init__(self, message: str = "未找到相关数据库表", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.SCHEMA_NOT_FOUND, message=message, detail=detail)


class SQLInjectionError(AppError):
    """SQL 注入检测错误"""
    def __init__(self, message: str = "检测到潜在的安全风险", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.SQL_INJECTION_DETECTED, message=message, detail=detail)


class TableNotAllowedError(AppError):
    """表不允许访问错误"""
    def __init__(self, message: str = "不允许访问该表", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.TABLE_NOT_ALLOWED, message=message, detail=detail)


class ReadonlyViolationError(AppError):
    """只读模式违规错误"""
    def __init__(self, message: str = "只读模式仅允许 SELECT 查询", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.READONLY_VIOLATION, message=message, detail=detail)


class RateLimitError(AppError):
    """请求限流错误"""
    def __init__(self, message: str = "请求过于频繁，请稍后重试", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.RATE_LIMITED, message=message, detail=detail)


class TimeoutError(AppError):
    """超时错误"""
    def __init__(self, message: str = "请求超时", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.TIMEOUT, message=message, detail=detail)


class DatabaseError(AppError):
    """数据库错误"""
    def __init__(self, message: str = "数据库操作失败", detail: Optional[str] = None):
        super().__init__(code=ErrorCode.DATABASE_ERROR, message=message, detail=detail)


# ============================================================================
# FastAPI 异常处理器注册
# ============================================================================

def register_error_handlers(app) -> None:
    """注册 FastAPI 全局异常处理器
    
    Args:
        app: FastAPI 应用实例
    """
    from fastapi.responses import JSONResponse
    from fastapi.requests import Request
    import logging
    
    logger = logging.getLogger(__name__)
    
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        """处理 AppError 异常"""
        logger.error(
            f"AppError: {exc.code.name}",
            extra={
                "error_code": exc.code.value,
                "error_message": exc.message,
                "error_detail": exc.detail,
                "error_context": exc.context,
                "request_path": str(request.url),
                "request_method": request.method,
            }
        )
        
        return JSONResponse(
            status_code=_get_status_code(exc.code),
            content=exc.to_response(),
        )
    
    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        """处理未捕获的异常"""
        logger.exception(
            f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
            extra={
                "request_path": str(request.url),
                "request_method": request.method,
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "服务器内部错误，请稍后重试",
                }
            }
        )


def _get_status_code(code: ErrorCode) -> int:
    """根据错误码获取 HTTP 状态码"""
    if code == ErrorCode.RATE_LIMITED:
        return 429
    elif code == ErrorCode.TIMEOUT:
        return 504
    elif code == ErrorCode.UNAUTHORIZED_ACCESS:
        return 401
    elif code.value < 3000:
        return 400
    else:
        return 500