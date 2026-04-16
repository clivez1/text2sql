from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent


@dataclass(frozen=True)
class PromptBundle:
    system_prompt: str
    user_prompt: str
    explanation_prompt: str


TEXT2SQL_SYSTEM_PROMPT = dedent(
    """
    你是一个面向中文业务问题的 Text2SQL 助手。
    目标是基于给定 schema 与示例 SQL，稳定生成可执行、可解释、只读的 SQLite 查询。

    规则：
    1. 只生成 SQL，不输出 Markdown 代码块。
    2. 优先单表查询；只有问题明确涉及商品明细、销量、销售额拆分时才考虑关联表。
    3. 严格使用已提供的表名与字段名，不要臆造字段。
    4. 默认生成 SELECT 语句；避免 INSERT/UPDATE/DELETE/DDL。
    5. 未明确要求全量数据时，优先补 LIMIT。
    6. 中文问题优先映射：
       - 订单/订单金额/客户/城市/区域 -> orders
       - 商品/品类 -> products
       - 订单明细/数量/单价 -> order_items
    7. 输出应便于后续解释：字段别名尽量语义化。
    """
).strip()


SQL_EXPLANATION_TEMPLATE = dedent(
    """
    请用简洁中文解释这条 SQL 的业务含义，输出 2-3 句：
    - 第一句说明查的是哪张表/哪些字段
    - 第二句说明筛选、分组、排序逻辑
    - 如有 LIMIT，说明这是为保证结果可读性
    SQL: {sql}
    """
).strip()


def build_prompt_bundle(question: str, schema_context: str, examples_context: str = "") -> PromptBundle:
    user_prompt = dedent(
        f"""
        用户问题：{question}

        Schema 上下文：
        {schema_context or '暂无 schema 上下文，请严格保守生成。'}

        示例 SQL：
        {examples_context or '暂无示例 SQL。'}

        请输出最终 SQL。
        """
    ).strip()
    explanation_prompt = SQL_EXPLANATION_TEMPLATE.format(sql=question)
    return PromptBundle(
        system_prompt=TEXT2SQL_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        explanation_prompt=explanation_prompt,
    )


def build_sql_explanation(sql: str, rule_hint: str | None = None) -> str:
    summary = f"该 SQL 以只读方式执行：{sql[:160]}"
    if rule_hint:
        return f"{rule_hint}；{summary}。"
    return summary + "。"
