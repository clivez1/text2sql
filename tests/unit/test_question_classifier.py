from app.core.nlu.question_classifier import classify_question


def test_classify_simple_lookup():
    result = classify_question('各城市订单数量')
    assert result.category == 'simple_lookup'
    assert result.needs_llm is False
    assert 'orders' in result.entities


def test_classify_ranked_aggregation():
    result = classify_question('上个月销售额最高的前5个产品是什么')
    assert result.category == 'ranked_aggregation'
    assert result.needs_llm is False
    assert '上个月' in result.time_phrases


def test_classify_complex_analysis():
    result = classify_question('请结合上个月趋势分析销售额最高的前5个产品')
    assert result.category == 'complex_analysis'
    assert result.needs_llm is True
