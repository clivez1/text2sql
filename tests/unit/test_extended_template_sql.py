from app.core.sql.generator import generate_sql_by_rules


def test_region_sales_template():
    sql, explanation = generate_sql_by_rules('统计华东区域销售额')
    assert 'FROM orders' in sql or 'FROM order_items' in sql
    assert '华东' in sql


def test_city_ranking_template():
    sql, explanation = generate_sql_by_rules('按城市统计订单数量并排序')
    assert 'GROUP BY city' in sql
    assert 'ORDER BY order_count DESC' in sql


def test_category_count_template():
    sql, explanation = generate_sql_by_rules('按类别统计商品数量')
    assert 'GROUP BY category' in sql
    assert 'FROM products' in sql
