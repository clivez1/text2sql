from app.core.retrieval.schema_loader import build_local_context


def test_build_local_context_contains_category_and_entities():
    context = build_local_context('各城市订单数量')
    assert 'question_category=simple_lookup' in context
    assert 'entities=orders' in context
    assert 'alias:订单数量' in context
    assert 'orders(' in context


def test_build_local_context_contains_time_and_product_aliases():
    context = build_local_context('上个月销售额最高的前5个产品是什么')
    assert 'time_phrases=上个月' in context
    assert 'alias:销售额' in context
    assert 'products(' in context
