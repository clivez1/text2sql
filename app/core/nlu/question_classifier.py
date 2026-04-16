from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class QuestionClassification:
    category: str
    entities: List[str] = field(default_factory=list)
    time_phrases: List[str] = field(default_factory=list)
    needs_llm: bool = False


TIME_PHRASES = ["上个月", "最近", "今年", "昨天", "今天"]
ENTITY_KEYWORDS = {
    "orders": ["订单", "城市", "区域", "客户", "金额"],
    "products": ["商品", "产品", "品类", "类别"],
    "order_items": ["明细", "销量", "数量", "单价"],
}


def classify_question(question: str) -> QuestionClassification:
    q = question.strip()
    time_phrases = [tp for tp in TIME_PHRASES if tp in q]

    entities = []
    for entity, keywords in ENTITY_KEYWORDS.items():
        if any(k in q for k in keywords):
            entities.append(entity)

    if any(k in q for k in ["趋势", "同比", "环比", "分析", "结合"]):
        return QuestionClassification(category="complex_analysis", entities=entities, time_phrases=time_phrases, needs_llm=True)

    if any(k in q for k in ["前5", "top", "排名", "销售额"]):
        return QuestionClassification(category="ranked_aggregation", entities=entities, time_phrases=time_phrases, needs_llm=False)

    if any(k in q for k in ["总数", "数量", "多少", "平均", "最高", "最低", "列出", "查看"]):
        return QuestionClassification(category="simple_lookup", entities=entities, time_phrases=time_phrases, needs_llm=False)

    return QuestionClassification(category="unknown", entities=entities, time_phrases=time_phrases, needs_llm=True)
