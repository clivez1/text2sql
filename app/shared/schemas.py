"""
Pydantic 模型定义

请求和响应的数据模型。
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional, List, Dict
from datetime import datetime

from pydantic import BaseModel, Field


# ============== 请求模型 ==============

class AskRequest(BaseModel):
    """自然语言查询请求"""
    question: str = Field(
        ...,
        description="自然语言问题",
        json_schema_extra={"example": "上个月销售额最高的前5个产品是什么？"},
    )
    session_id: Optional[str] = Field(
        None,
        description="会话ID，用于多轮对话",
        json_schema_extra={"example": "user-001"},
    )
    explain: bool = Field(
        True,
        description="是否返回 SQL 解释"
    )


class ChartConfig(BaseModel):
    """图表配置"""
    chart_type: str = Field(..., description="图表类型: bar/line/pie/scatter/table")
    x_column: Optional[str] = Field(None, description="X 轴列名")
    y_column: Optional[str] = Field(None, description="Y 轴列名")
    y_columns: List[str] = Field(default_factory=list, description="Y 轴列名列表")
    color_column: Optional[str] = Field(None, description="颜色分组列")
    confidence: float = Field(0.5, description="推荐置信度")


# ============== 响应模型 ==============

class AskResponse(BaseModel):
    """查询响应"""
    success: bool = Field(True, description="请求是否成功")
    question: str = Field(..., description="用户问题")
    generated_sql: str = Field(..., description="生成的 SQL")
    mode: str = Field(..., description="运行模式: llm/fallback")
    blocked_reason: Optional[str] = Field(None, description="拦截原因")
    sql_explanation: str = Field("", description="SQL 解释")
    result_preview: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="查询结果预览"
    )
    row_count: int = Field(0, description="结果行数")
    execution_time_ms: float = Field(0, description="执行时间(毫秒)")
    chart: Optional[ChartConfig] = Field(None, description="图表推荐")
    error: Optional[str] = Field(None, description="错误信息")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态: ok/error")
    db_type: str = Field(..., description="数据库类型")
    db_connected: bool = Field(..., description="数据库连接状态")
    llm_available: bool = Field(False, description="LLM 可用状态")
    llm_provider: Optional[str] = Field(None, description="LLM 提供商")
    llm_latency_ms: Optional[float] = Field(None, description="LLM 检测延迟(毫秒)")
    latency_ms: float = Field(..., description="响应延迟(毫秒)")
    version: str = Field("3.0", description="API 版本")
    timestamp: str = Field(..., description="时间戳")


class SchemaResponse(BaseModel):
    """Schema 响应"""
    tables: Dict[str, List[str]] = Field(
        ...,
        description="表名到列名的映射"
    )
    ddl: Optional[str] = Field(None, description="DDL 语句")


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(False)
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")


# ============== 内部数据类 ==============

@dataclass
class AskResult:
    """查询结果（内部使用）"""
    question: str
    generated_sql: str
    mode: str
    blocked_reason: Optional[str]
    sql_explanation: str
    result_preview: list[dict[str, Any]]
    chart_config: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============== 辅助函数 ==============

def create_ask_response(
    result: AskResult,
    execution_time_ms: float = 0,
    chart_config: Optional[Dict[str, Any]] = None,
) -> AskResponse:
    """创建 AskResponse"""
    return AskResponse(
        success=True,
        question=result.question,
        generated_sql=result.generated_sql,
        mode=result.mode,
        blocked_reason=result.blocked_reason,
        sql_explanation=result.sql_explanation,
        result_preview=result.result_preview,
        row_count=len(result.result_preview),
        execution_time_ms=execution_time_ms,
        chart=ChartConfig(**chart_config) if chart_config else None,
    )