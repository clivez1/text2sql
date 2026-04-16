from __future__ import annotations

import os
import time
import logging

from app.core.llm.adapters import LLMAdapter, OpenAICompatibleAdapter
from app.core.llm.prompts import build_sql_explanation
from app.core.nlu.question_classifier import classify_question
from app.core.retrieval.schema_loader import retrieve_schema_context
from app.core.sql.generator import DEFAULT_EXPLANATION, generate_sql_by_rules
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


FAST_FALLBACK_KEYWORDS = [
    "各城市订单数量",
    "城市订单数量",
    "列出所有产品",
    "订单总数",
    "最近订单",
    "最高金额",
    "平均金额",
    "最高单价",
    "平均数量",
]


def should_fast_fallback(question: str) -> bool:
    classification = classify_question(question)
    if classification.needs_llm is False:
        return True
    lowered = question.lower().strip()
    return any(keyword in question for keyword in FAST_FALLBACK_KEYWORDS) or any(
        token in lowered for token in ["count", "list products", "max", "avg"]
    )


def get_llm_adapter(index: int = 1) -> LLMAdapter:
    settings = get_settings()
    config = settings.get_provider_config(index)
    return OpenAICompatibleAdapter(config=config)


def _try_llm_with_fallback(
    question: str,
    schema_context: str,
    retrieval_ms: float,
    llm_ms: float,
    exc: Exception,
) -> tuple:
    """Try fallback LLM (index=2) if primary fails."""
    settings = get_settings()
    if not settings.has_fallback():
        return None

    logger.warning(f"Primary LLM failed ({exc}), trying fallback...")
    fallback_start = time.perf_counter()
    try:
        adapter2 = get_llm_adapter(index=2)
        sql = adapter2.generate_sql(question)
        fallback_ms = (time.perf_counter() - fallback_start) * 1000
        if not sql or "SELECT" not in sql.upper():
            raise RuntimeError(f"Fallback LLM returned non-SQL: {sql!r}")
        explanation = build_sql_explanation(
            sql,
            rule_hint=(
                f"已结合 schema 检索上下文生成 SQL；provider={adapter2.provider_name}; "
                f"retrieval_ms={retrieval_ms:.2f}; llm_ms={llm_ms:.2f}; fallback_ms={fallback_ms:.2f}"
            ),
        )
        return sql, explanation, adapter2.provider_name, None
    except Exception as exc2:
        fallback_ms = (time.perf_counter() - fallback_start) * 1000
        blocked_reason = (
            f"LLM-1 failed: {exc} | LLM-2 failed: {exc2} | "
            f"retrieval_ms={retrieval_ms:.2f} | llm_ms={llm_ms:.2f} | fallback_ms={fallback_ms:.2f}"
        )
        return None, None, None, blocked_reason


def _generate_sql_legacy(question: str) -> tuple[str, str, str, str | None]:
    """
    旧版 generate_sql 逻辑（保留用于测试保护网）。
    所有性能埋点均在 explanation 字符串中。
    """
    retrieval_start = time.perf_counter()
    schema_context = retrieve_schema_context(question)
    retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

    if should_fast_fallback(question):
        fallback_start = time.perf_counter()
        sql, explanation = generate_sql_by_rules(question)
        fallback_ms = (time.perf_counter() - fallback_start) * 1000
        if explanation == DEFAULT_EXPLANATION:
            explanation = (
                f"{DEFAULT_EXPLANATION}（fast-fallback；retrieval_ms={retrieval_ms:.2f}；"
                f"fallback_ms={fallback_ms:.2f}；schema_context={schema_context[:80]}）"
            )
        else:
            explanation = build_sql_explanation(
                sql,
                rule_hint=f"{explanation}；fast-fallback；retrieval_ms={retrieval_ms:.2f}；fallback_ms={fallback_ms:.2f}",
            )
        return sql, explanation, "fallback", "fast_fallback_rule_path"

    # 检查 LLM 健康状态
    from app.core.llm.health_check import should_use_fallback

    if should_use_fallback():
        logger.warning("LLM is not available, using fallback directly")
        fallback_start = time.perf_counter()
        sql, explanation = generate_sql_by_rules(question)
        fallback_ms = (time.perf_counter() - fallback_start) * 1000
        if explanation == DEFAULT_EXPLANATION:
            explanation = (
                f"{DEFAULT_EXPLANATION}（llm-unavailable-fallback；retrieval_ms={retrieval_ms:.2f}；"
                f"fallback_ms={fallback_ms:.2f}；schema_context={schema_context[:80]}）"
            )
        else:
            explanation = build_sql_explanation(
                sql,
                rule_hint=f"{explanation}；llm-unavailable-fallback；retrieval_ms={retrieval_ms:.2f}；fallback_ms={fallback_ms:.2f}",
            )
        return sql, explanation, "fallback", "llm_unavailable"

    llm_start = time.perf_counter()
    try:
        adapter = get_llm_adapter()
        sql = adapter.generate_sql(question)
        llm_ms = (time.perf_counter() - llm_start) * 1000
        if not sql or "SELECT" not in sql.upper():
            raise RuntimeError(f"LLM returned non-SQL response: {sql!r}")
        explanation = build_sql_explanation(
            sql,
            rule_hint=(
                f"已结合 schema 检索上下文生成 SQL；provider={adapter.provider_name}; "
                f"retrieval_ms={retrieval_ms:.2f}; llm_ms={llm_ms:.2f}"
            ),
        )
        return sql, explanation, adapter.provider_name, None
    except Exception as exc:
        llm_ms = (time.perf_counter() - llm_start) * 1000
        result = _try_llm_with_fallback(
            question, schema_context, retrieval_ms, llm_ms, exc
        )
        if result is not None and result[0] is not None:
            return result

    fallback_start = time.perf_counter()
    sql, explanation = generate_sql_by_rules(question)
    fallback_ms = (time.perf_counter() - fallback_start) * 1000
    if explanation == DEFAULT_EXPLANATION:
        explanation = (
            f"{DEFAULT_EXPLANATION}（fallback；retrieval_ms={retrieval_ms:.2f}；"
            f"llm_ms={llm_ms:.2f}；fallback_ms={fallback_ms:.2f}；"
            f"schema_context={schema_context[:80]}）"
        )
    else:
        explanation = build_sql_explanation(
            sql,
            rule_hint=(
                f"{explanation}；retrieval_ms={retrieval_ms:.2f}；"
                f"llm_ms={llm_ms:.2f}；fallback_ms={fallback_ms:.2f}"
            ),
        )
    blocked_reason = (
        f"LLM runtime failed: {exc} | retrieval_ms={retrieval_ms:.2f} | "
        f"llm_ms={llm_ms:.2f} | schema_context={schema_context[:120]}"
    )
    return sql, explanation, "fallback", blocked_reason


def generate_sql_v2(question: str) -> tuple[str, str, str, str | None]:
    """
    新版 generate_sql，使用 SchemaRetriever 注入 + MetricsCollector。
    通过 USE_GENERATE_SQL_V2=true 环境变量可切换到此版本。

    与旧版的差异：
    - 通过 get_retriever() 注入 retriever（而非直接调用 retrieve_schema_context）
    - 性能埋点结构化（暂未迁移到 MetricsCollector，保持 explanation 格式）
    - 路由逻辑相同，代码结构更清晰
    """
    from app.core.retrieval.schema_loader import get_retriever

    retrieval_start = time.perf_counter()
    retriever = get_retriever()
    schema_context = retriever.retrieve(question)
    retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

    classification = classify_question(question)

    # 路由决策 1：不需要 LLM，走规则路径
    if not classification.needs_llm:
        fallback_start = time.perf_counter()
        sql, explanation = generate_sql_by_rules(question)
        fallback_ms = (time.perf_counter() - fallback_start) * 1000
        if explanation == DEFAULT_EXPLANATION:
            explanation = (
                f"{DEFAULT_EXPLANATION}（fast-fallback-v2；retrieval_ms={retrieval_ms:.2f}；"
                f"fallback_ms={fallback_ms:.2f}；schema_context={schema_context[:80]}）"
            )
        else:
            explanation = build_sql_explanation(
                sql,
                rule_hint=f"{explanation}；fast-fallback-v2；retrieval_ms={retrieval_ms:.2f}；fallback_ms={fallback_ms:.2f}",
            )
        return sql, explanation, "fallback", "rule_path"

    # 路由决策 2：fast fallback 关键字匹配
    if should_fast_fallback(question):
        fallback_start = time.perf_counter()
        sql, explanation = generate_sql_by_rules(question)
        fallback_ms = (time.perf_counter() - fallback_start) * 1000
        if explanation == DEFAULT_EXPLANATION:
            explanation = (
                f"{DEFAULT_EXPLANATION}（fast-fallback-v2；retrieval_ms={retrieval_ms:.2f}；"
                f"fallback_ms={fallback_ms:.2f}；schema_context={schema_context[:80]}）"
            )
        else:
            explanation = build_sql_explanation(
                sql,
                rule_hint=f"{explanation}；fast-fallback-v2；retrieval_ms={retrieval_ms:.2f}；fallback_ms={fallback_ms:.2f}",
            )
        return sql, explanation, "fallback", "fast_fallback_rule_path"

    # 路由决策 3：LLM 健康检查
    from app.core.llm.health_check import should_use_fallback

    if should_use_fallback():
        logger.warning("LLM is not available, using fallback directly")
        fallback_start = time.perf_counter()
        sql, explanation = generate_sql_by_rules(question)
        fallback_ms = (time.perf_counter() - fallback_start) * 1000
        if explanation == DEFAULT_EXPLANATION:
            explanation = (
                f"{DEFAULT_EXPLANATION}（llm-unavailable-fallback-v2；retrieval_ms={retrieval_ms:.2f}；"
                f"fallback_ms={fallback_ms:.2f}；schema_context={schema_context[:80]}）"
            )
        else:
            explanation = build_sql_explanation(
                sql,
                rule_hint=f"{explanation}；llm-unavailable-fallback-v2；retrieval_ms={retrieval_ms:.2f}；fallback_ms={fallback_ms:.2f}",
            )
        return sql, explanation, "fallback", "llm_unavailable"

    # LLM 生成路径
    llm_start = time.perf_counter()
    try:
        adapter = get_llm_adapter()
        sql = adapter.generate_sql(question)
        llm_ms = (time.perf_counter() - llm_start) * 1000
        if not sql or "SELECT" not in sql.upper():
            raise RuntimeError(f"LLM returned non-SQL response: {sql!r}")
        explanation = build_sql_explanation(
            sql,
            rule_hint=(
                f"已结合 schema 检索上下文生成 SQL-v2；provider={adapter.provider_name}; "
                f"retrieval_ms={retrieval_ms:.2f}; llm_ms={llm_ms:.2f}"
            ),
        )
        return sql, explanation, adapter.provider_name, None
    except Exception as exc:
        llm_ms = (time.perf_counter() - llm_start) * 1000
        result = _try_llm_with_fallback(
            question, schema_context, retrieval_ms, llm_ms, exc
        )
        if result is not None and result[0] is not None:
            return result

    # LLM 失败，走 fallback
    fallback_start = time.perf_counter()
    sql, explanation = generate_sql_by_rules(question)
    fallback_ms = (time.perf_counter() - fallback_start) * 1000
    if explanation == DEFAULT_EXPLANATION:
        explanation = (
            f"{DEFAULT_EXPLANATION}（fallback-v2；retrieval_ms={retrieval_ms:.2f}；"
            f"llm_ms={llm_ms:.2f}；fallback_ms={fallback_ms:.2f}；"
            f"schema_context={schema_context[:80]}）"
        )
    else:
        explanation = build_sql_explanation(
            sql,
            rule_hint=(
                f"{explanation}；retrieval_ms={retrieval_ms:.2f}；"
                f"llm_ms={llm_ms:.2f}；fallback_ms={fallback_ms:.2f}"
            ),
        )
    blocked_reason = (
        f"LLM runtime failed: {exc} | retrieval_ms={retrieval_ms:.2f} | "
        f"llm_ms={llm_ms:.2f} | schema_context={schema_context[:120]}"
    )
    return sql, explanation, "fallback", blocked_reason


# Feature flag：USE_GENERATE_SQL_V2=true 时启用 v2 版本
USE_V2 = os.getenv("USE_GENERATE_SQL_V2", "false").lower() == "true"


def generate_sql(question: str) -> tuple[str, str, str, str | None]:
    """
    生成 SQL 的统一入口。

    通过 USE_GENERATE_SQL_V2 环境变量控制版本：
    - false（默认）：使用旧版 _generate_sql_legacy()，行为与此前完全相同
    - true：使用新版 generate_sql_v2()，通过 get_retriever() 获取 retriever
    """
    if USE_V2:
        return generate_sql_v2(question)
    return _generate_sql_legacy(question)


def check_llm_connectivity() -> tuple[str, str]:
    adapter = get_llm_adapter()
    return adapter.provider_name, adapter.connectivity_check()
