from app.core.sql.generator import generate_sql_by_rules


def test_template_sql_city_order_count():
    sql, explanation = generate_sql_by_rules('请统计各城市订单数量')
    assert 'GROUP BY city' in sql
    assert 'COUNT(*) AS order_count' in sql
    assert '本地语义映射' in explanation


def test_template_sql_top5_sales_last_month():
    sql, explanation = generate_sql_by_rules('上个月销售额最高的前5个产品')
    assert 'JOIN products' in sql
    assert 'LIMIT 5' in sql
    assert '本地语义映射' in explanation or 'Top5' in explanation
