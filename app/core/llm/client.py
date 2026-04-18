from __future__ import annotations

import time
import logging

from app.core.llm.adapters import LLMAdapter, create_llm_adapter
from app.core.llm.prompts import build_sql_explanation
from app.core.nlu.question_classifier import classify_question
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
    return create_llm_adapter(config)


def _try_llm_cascade(
    question: str,
    schema_context: str,
    retrieval_ms: float,
    llm_ms: float,
    primary_error: Exception,
) -> tuple | None:
    """
    Try fallback providers 2..N in sequence after primary provider fails.

    Returns:
        tuple (sql, explanation, provider_name, None) on success
        None if all fallback providers exhausted
    """
    settings = get_settings()
    if not settings.has_fallback():
        return None

    logger.warning(f"Primary LLM failed ({primary_error}), trying fallback cascade...")

    for idx in range(2, settings.provider_count + 1):
        fallback_start = time.perf_counter()
        try:
            adapter = get_llm_adapter(index=idx)
            sql = adapter.generate_sql(question, schema_context)
            fallback_ms = (time.perf_counter() - fallback_start) * 1000
            if not sql or "SELECT" not in sql.upper():
                raise RuntimeError(f"Provider {idx} returned non-SQL: {sql!r}")
            explanation = build_sql_explanation(
                sql,
                rule_hint=(
                    f"已结合 schema 检索上下文生成 SQL；provider={adapter.provider_name}; "
                    f"fallback_index={idx}; retrieval_ms={retrieval_ms:.2f}; "
                    f"llm_ms={llm_ms:.2f}; fallback_ms={fallback_ms:.2f}"
                ),
            )
            return sql, explanation, adapter.provider_name, None
        except Exception as exc:
            fallback_ms = (time.perf_counter() - fallback_start) * 1000
            logger.warning(f"Fallback provider {idx} failed: {exc}")
            continue

    # All fallback providers exhausted
    return None


def generate_sql(question: str) -> tuple[str, str, str, str | None]:
    """
    Generate SQL from natural language question.

    Flow:
    1. Retrieve schema context via get_retriever()
    2. Check if fast-fallback (rule-based) path applies
    3. Check LLM health status
    4. Try primary LLM provider
    5. On failure, cascade through fallback providers 2..N
    6. If all LLMs fail, fall back to rule-based generation

    Returns:
        tuple (sql, explanation, provider_name, blocked_reason)
    """
    # Step 1: Retrieve schema context
    from app.core.retrieval.schema_loader import get_retriever

    retrieval_start = time.perf_counter()
    retriever = get_retriever()
    schema_context = retriever.retrieve(question)
    retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

    classification = classify_question(question)

    # Step 2: Fast-fallback path (rule-based)
    if not classification.needs_llm or should_fast_fallback(question):
        fallback_reason = (
            "rule_path" if not classification.needs_llm else "fast_fallback_rule_path"
        )
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
        return sql, explanation, "fallback", fallback_reason

    # Step 3: Check LLM health status
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

    # Step 4: Try primary LLM provider
    llm_start = time.perf_counter()
    try:
        adapter = get_llm_adapter()
        sql = adapter.generate_sql(question, schema_context)
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

        # Step 5: Try fallback cascade 2..N
        result = _try_llm_cascade(question, schema_context, retrieval_ms, llm_ms, exc)
        if result is not None and result[0] is not None:
            return result

        # Step 6: All LLMs failed, use rule-based fallback
        blocked_reason = (
            result[3]
            if result
            else (
                f"LLM runtime failed: {exc} | retrieval_ms={retrieval_ms:.2f} | "
                f"llm_ms={llm_ms:.2f} | schema_context={schema_context[:120]}"
            )
        )
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
        return sql, explanation, "fallback", blocked_reason


def check_llm_connectivity() -> tuple[str, str]:
    adapter = get_llm_adapter()
    return adapter.provider_name, adapter.connectivity_check()
