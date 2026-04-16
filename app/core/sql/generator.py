from __future__ import annotations

from app.core.sql.local_semantics import extract_metric_alias, extract_time_condition
from app.rules import RuleStore


DEFAULT_SQL = "SELECT order_id, order_date, customer_name, city, total_amount FROM orders ORDER BY order_date DESC LIMIT 10;"
DEFAULT_EXPLANATION = "未命中特定规则，回退为最近订单列表，确保链路可运行。"


def try_template_sql(question: str) -> tuple[str, str] | None:
    metric = extract_metric_alias(question)
    time_condition = extract_time_condition(question)

    if metric == 'COUNT(*)' and '城市' in question:
        return (
            "SELECT city, COUNT(*) AS order_count FROM orders GROUP BY city ORDER BY order_count DESC LIMIT 10;",
            "基于本地语义映射生成：按城市统计订单量。",
        )

    if metric == 'SUM(oi.quantity * oi.unit_price)' and '产品' in question and '前5' in question:
        where_clause = f"WHERE {time_condition}" if time_condition else ""
        return (
            f"SELECT p.product_name, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue FROM order_items oi JOIN orders o ON oi.order_id = o.order_id JOIN products p ON oi.product_id = p.product_id {where_clause} GROUP BY p.product_name ORDER BY revenue DESC LIMIT 5;",
            "基于本地语义映射生成：按产品统计销售额并取 Top5。",
        )

    if '区域' in question and '销售额' in question and any(region in question for region in ['华东', '华南', '华北']):
        region = next(region for region in ['华东', '华南', '华北'] if region in question)
        return (
            f"SELECT region, ROUND(SUM(total_amount), 2) AS revenue FROM orders WHERE region = '{region}' GROUP BY region LIMIT 50;",
            "基于本地语义映射生成：按区域统计销售额。",
        )

    if '类别' in question and ('商品数量' in question or '商品' in question):
        return (
            "SELECT category, COUNT(*) AS product_count FROM products GROUP BY category ORDER BY product_count DESC LIMIT 20;",
            "基于本地语义映射生成：按类别统计商品数量。",
        )

    return None


def generate_sql_by_rules(question: str) -> tuple[str, str]:
    normalized = question.replace('？', '').replace('?', '').strip()

    templated = try_template_sql(normalized)
    if templated:
        return templated

    # 从 RuleStore YAML 匹配
    store = RuleStore.get_instance()
    matched = store.match(normalized)
    if matched:
        return matched

    return DEFAULT_SQL, DEFAULT_EXPLANATION
