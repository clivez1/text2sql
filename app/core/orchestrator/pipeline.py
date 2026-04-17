from __future__ import annotations

import json
import sys
import time
from app.core.llm.client import generate_sql
from app.core.sql.executor import run_query
from app.core.metrics import start_request, end_request, record_stage
from app.shared.schemas import AskResult


def generate_sql_preview(question: str, trace_id: str = None) -> dict:
    """
    第一步：仅生成 SQL 并返回预览，不执行查询。

    Returns:
        dict with keys: question, sql, explanation, mode, blocked_reason, trace_id, generate_ms
    """
    if trace_id is None:
        trace_id = start_request("/ask")

    generate_start = time.perf_counter()
    sql, explanation, mode, blocked_reason = generate_sql(question)
    generate_ms = (time.perf_counter() - generate_start) * 1000
    record_stage(trace_id, "sql_generation", generate_ms)

    return {
        "question": question,
        "sql": sql,
        "explanation": explanation,
        "mode": mode,
        "blocked_reason": blocked_reason,
        "trace_id": trace_id,
        "generate_ms": generate_ms,
    }


def execute_confirmed_sql(preview: dict) -> AskResult:
    """
    第二步：用户确认后执行 SQL 并返回完整结果。

    Args:
        preview: generate_sql_preview() 的返回值

    Returns:
        AskResult
    """
    sql = preview["sql"]
    question = preview["question"]
    explanation = preview["explanation"]
    mode = preview["mode"]
    blocked_reason = preview["blocked_reason"]
    trace_id = preview.get("trace_id", "")
    generate_ms = preview.get("generate_ms", 0)

    query_start = time.perf_counter()
    df = run_query(sql)
    query_ms = (time.perf_counter() - query_start) * 1000
    if trace_id:
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


def ask_question(question: str, trace_id: str = None) -> AskResult:
    """
    一步完成查询（向后兼容接口，供 API 使用）。
    """
    preview = generate_sql_preview(question, trace_id)
    return execute_confirmed_sql(preview)


def summarize_result_natural_language(question: str, df_records: list, sql: str) -> str:
    """
    将查询结果转换为自然语言摘要。

    优先使用 LLM 生成，失败时回退到模板。
    """
    import pandas as pd
    df = pd.DataFrame(df_records)

    if df.empty:
        return "查询结果为空，未找到匹配的数据。"

    # 尝试使用 LLM 生成摘要
    try:
        summary = _llm_summarize(question, df, sql)
        if summary:
            return summary
    except Exception:
        pass

    # 回退到模板摘要
    return _template_summarize(question, df)


def _llm_summarize(question: str, df, sql: str) -> str | None:
    """使用 LLM 生成自然语言摘要"""
    from app.core.llm.health_check import should_use_fallback

    if should_use_fallback():
        return None

    try:
        from app.core.llm.client import get_llm_adapter

        adapter = get_llm_adapter()
        # 构造数据摘要（不发送全部数据以节省 token）
        data_preview = df.head(20).to_string(index=False)
        prompt = (
            f"用户的问题是：{question}\n"
            f"执行的 SQL：{sql}\n"
            f"查询结果（前 {min(20, len(df))} 行）：\n{data_preview}\n"
            f"共 {len(df)} 行数据。\n\n"
            f"请用简洁的中文自然语言回答用户的问题，直接给出答案，不要重复问题。"
        )
        response = adapter.chat(prompt)
        if response and len(response.strip()) > 5:
            return response.strip()
    except Exception:
        pass
    return None


def _template_summarize(question: str, df) -> str:
    """模板化自然语言摘要"""
    row_count = len(df)
    col_count = len(df.columns)
    columns = ", ".join(df.columns[:5])

    summary_parts = [f"查询返回了 {row_count} 条记录"]

    if col_count <= 5:
        summary_parts.append(f"包含字段：{columns}")

    # 数值列统计
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        for col in numeric_cols[:3]:
            total = df[col].sum()
            avg = df[col].mean()
            summary_parts.append(f"{col} 合计 {total:,.2f}（平均 {avg:,.2f}）")

    # 第一行预览
    if row_count > 0:
        first_row = df.iloc[0]
        top_info = "，".join(f"{k}={v}" for k, v in first_row.items() if str(v).strip())
        summary_parts.append(f"排名第一：{top_info[:100]}")

    return "。".join(summary_parts) + "。"


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "上个月销售额最高的前5个产品是什么？"
    result = ask_question(question)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
