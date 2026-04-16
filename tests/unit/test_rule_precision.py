from app.core.sql.generator import generate_sql_by_rules


def test_city_order_count_rule_precision():
    sql, explanation = generate_sql_by_rules("各城市订单数量")
    assert "COUNT(*) AS order_count" in sql
    assert "FROM orders" in sql
    assert "GROUP BY city" in sql


def test_list_all_products_rule_precision():
    sql, explanation = generate_sql_by_rules("列出所有产品")
    assert "FROM products" in sql
    assert "product_name" in sql


def test_top5_sales_rule_precision():
    sql, explanation = generate_sql_by_rules("上个月销售额最高的前5个产品是什么")
    assert "JOIN products" in sql
    assert "LIMIT 5" in sql
