"""
Text2SQL Agent FastAPI 应用

提供 REST API 接口：
- POST /ask - 自然语言查询
- GET /health - 健康检查
- GET /schemas - 获取数据库 schema
- GET /metrics - 获取可观测性指标
- GET / - API 信息
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, inspect, text

from app.config.settings import get_settings
from app.core.orchestrator.pipeline import ask_question
from app.core.metrics import start_request, end_request, record_stage, get_metrics
from app.core.auth.middleware import APIKeyMiddleware
from app.core.llm.health_check import check_llm_health, is_llm_available
from app.core.errors import register_error_handlers
from app.shared.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    SchemaResponse,
    create_ask_response,
)


app = FastAPI(
    title="Text2SQL Agent API",
    description="自然语言转 SQL 查询服务",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加 API Key 认证中间件
app.add_middleware(APIKeyMiddleware)


@app.on_event("startup")
async def startup_event():
    """应用启动时执行 LLM 健康检测"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Starting LLM health check on startup...")

    # 注册全局错误处理器
    register_error_handlers(app)
    logger.info("Error handlers registered.")

    # 异步执行健康检测（不阻塞启动）
    try:
        status = check_llm_health(timeout_seconds=15.0)
        if status.available:
            logger.info(f"LLM is available: {status.provider} ({status.latency_ms:.0f}ms)")
        else:
            logger.warning(f"LLM is not available: {status.error}. Will use fallback.")
    except Exception as e:
        logger.warning(f"LLM health check failed: {e}. Will use fallback.")


@app.get("/", tags=["Root"])
def root() -> dict:
    return {
        "name": "Text2SQL Agent API",
        "version": "3.0.0",
        "docs": "/docs",
        "endpoints": {
            "ask": "POST /ask",
            "health": "GET /health",
            "schemas": "GET /schemas",
            "metrics": "GET /metrics",
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health() -> HealthResponse:
    start_time = time.time()
    settings = get_settings()

    try:
        engine = create_engine(settings.db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
        db_type = "sqlite" if "sqlite" in settings.db_url.lower() else "mysql"
    except Exception:
        db_connected = False
        db_type = "unknown"

    # 获取 LLM 状态
    from app.core.llm.health_check import get_llm_health_checker
    llm_checker = get_llm_health_checker()
    llm_status = llm_checker.get_status()

    llm_available = llm_status.available if llm_status else False
    llm_provider = llm_status.provider if llm_status else None
    llm_latency_ms = llm_status.latency_ms if llm_status else None

    latency_ms = (time.time() - start_time) * 1000

    return HealthResponse(
        status="ok" if db_connected else "error",
        db_type=db_type,
        db_connected=db_connected,
        llm_available=llm_available,
        llm_provider=llm_provider,
        llm_latency_ms=llm_latency_ms,
        latency_ms=round(latency_ms, 2),
        timestamp=datetime.now().isoformat(),
    )


@app.get("/metrics", tags=["System"])
def metrics() -> dict:
    """获取可观测性指标"""
    return get_metrics()


@app.get("/schemas", response_model=SchemaResponse, tags=["Database"])
def get_schemas() -> SchemaResponse:
    settings = get_settings()

    try:
        engine = create_engine(settings.db_url)
        inspector = inspect(engine)

        tables = {}
        for table_name in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            tables[table_name] = columns

        ddl_parts = []
        for table_name, columns in tables.items():
            ddl_parts.append(f"-- {table_name}\n({', '.join(columns)})")

        return SchemaResponse(
            tables=tables,
            ddl="\n\n".join(ddl_parts),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Schema 失败: {str(e)}")


@app.post("/ask", response_model=AskResponse, tags=["Query"])
def ask(request: AskRequest) -> AskResponse:
    trace_id = start_request("/ask")
    start_time = time.time()

    try:
        pipeline_start = time.perf_counter()
        result = ask_question(request.question)
        pipeline_ms = (time.perf_counter() - pipeline_start) * 1000
        record_stage(trace_id, "pipeline", pipeline_ms)

        execution_time_ms = (time.time() - start_time) * 1000
        response = create_ask_response(
            result,
            execution_time_ms=execution_time_ms,
            chart_config=result.chart_config,
        )
        response.sql_explanation = (
            f"{response.sql_explanation} | trace={trace_id} | pipeline_ms={pipeline_ms:.2f}"
        )
        end_request(trace_id, "success")
        return response
    except Exception as e:
        end_request(trace_id, "error", str(e))
        return AskResponse(
            success=False,
            question=request.question,
            generated_sql="",
            mode="error",
            sql_explanation=f"trace={trace_id}",
            result_preview=[],
            error=str(e),
        )


@app.get("/ask", response_model=AskResponse, tags=["Query"])
def ask_get(
    question: str = Query(..., description="自然语言问题"),
    session_id: Optional[str] = Query(None, description="会话ID"),
) -> AskResponse:
    return ask(AskRequest(question=question, session_id=session_id))


@app.get("/metrics", tags=["Observability"])
def metrics_endpoint() -> dict:
    """获取可观测性指标"""
    return get_metrics()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
