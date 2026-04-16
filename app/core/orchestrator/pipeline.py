from __future__ import annotations

import json
import sys
import time
from app.core.llm.client import generate_sql
from app.core.sql.executor import run_query
from app.core.metrics import start_request, end_request, record_stage
from app.shared.schemas import AskResult


def ask_question(question: str, trace_id: str = None) -> AskResult:
    # 如果没有 trace_id，创建一个
    if trace_id is None:
        trace_id = start_request("/ask")

    generate_start = time.perf_counter()
    sql, explanation, mode, blocked_reason = generate_sql(question)
    generate_ms = (time.perf_counter() - generate_start) * 1000
    record_stage(trace_id, "sql_generation", generate_ms)

    query_start = time.perf_counter()
    df = run_query(sql)
    query_ms = (time.perf_counter() - query_start) * 1000
    record_stage(trace_id, "query_execution", query_ms)

    explanation = f"{explanation} | pipeline_generate_ms={generate_ms:.2f} | pipeline_query_ms={query_ms:.2f}"

    # ChartRecommender 下沉到 pipeline 层
    chart_config = None
    if not df.empty:
        try:
            from app.core.chart.recommender import ChartRecommender
            recommender = ChartRecommender()
            recommendation = recommender.recommend(df, question)
            chart_config = {
                "chart_type": recommendation.chart_type.value,
                "x_column": recommendation.x_column,
                "y_column": recommendation.y_column,
                "y_columns": recommendation.y_columns,
                "color_column": recommendation.color_column,
                "confidence": recommendation.confidence,
            }
        except Exception:
            # chart 生成失败不影响主流程
            chart_config = None

    return AskResult(
        question=question,
        generated_sql=sql,
        mode=mode,
        blocked_reason=blocked_reason,
        sql_explanation=explanation,
        result_preview=df.to_dict(orient="records"),
        chart_config=chart_config,
    )


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "上个月销售额最高的前5个产品是什么？"
    result = ask_question(question)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
