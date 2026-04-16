from app.core.sql.local_semantics import extract_time_condition, extract_metric_alias


def test_extract_time_condition_last_month():
    cond = extract_time_condition('上个月销售额最高的前5个产品')
    assert 'strftime' in cond


def test_extract_metric_alias_sales():
    metric = extract_metric_alias('销售额最高的产品')
    assert 'quantity * unit_price' in metric or 'SUM(oi.quantity * oi.unit_price)' in metric


def test_extract_metric_alias_order_count():
    metric = extract_metric_alias('各城市订单数量')
    assert metric == 'COUNT(*)'
