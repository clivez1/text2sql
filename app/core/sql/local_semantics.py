from __future__ import annotations

TIME_PHRASE_SQL = {
    "上个月": "strftime('%Y-%m', o.order_date) = (SELECT strftime('%Y-%m', date(MAX(order_date), 'start of month', '-1 month')) FROM orders)",
    "最近": "1=1",
}

FIELD_ALIASES = {
    "销售额": "SUM(oi.quantity * oi.unit_price)",
    "订单数量": "COUNT(*)",
    "订单量": "COUNT(*)",
    "平均金额": "AVG(total_amount)",
    "最高金额": "MAX(total_amount)",
    "最低金额": "MIN(total_amount)",
    "最高单价": "MAX(unit_price)",
    "平均数量": "AVG(quantity)",
}


def extract_time_condition(question: str) -> str | None:
    for phrase, condition in TIME_PHRASE_SQL.items():
        if phrase in question:
            return condition
    return None


def extract_metric_alias(question: str) -> str | None:
    for phrase, metric in FIELD_ALIASES.items():
        if phrase in question:
            return metric
    return None
