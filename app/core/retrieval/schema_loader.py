from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

from app.config.settings import get_settings
from app.core.nlu.question_classifier import classify_question
from app.core.retrieval.chroma_retriever import ChromaSchemaRetriever


FIELD_ALIASES = {
    "销售额": ["total_amount", "revenue", "quantity * unit_price"],
    "订单数量": ["COUNT(*)", "order_count"],
    "城市": ["city"],
    "区域": ["region"],
    "客户": ["customer_name"],
    "商品": ["product_name", "category"],
    "数量": ["quantity"],
    "单价": ["unit_price"],
}


# 单例 retriever 实例
_retriever_instance: ChromaSchemaRetriever | None = None


def get_retriever() -> ChromaSchemaRetriever:
    """获取 SchemaRetriever 单例实例"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = ChromaSchemaRetriever()
    return _retriever_instance


def load_schema_text() -> str:
    base = Path(__file__).resolve().parents[3]
    ddl = base / "data" / "ddl" / "sales_schema.sql"
    return ddl.read_text(encoding="utf-8") if ddl.exists() else ""


def load_schema_documents(limit: int = 8) -> list[dict[str, Any]]:
    settings = get_settings()
    client = chromadb.PersistentClient(path=str(Path(settings.vector_db_path) / "schema_store"))
    try:
        collection = client.get_collection("schema_docs")
    except Exception:
        return []

    payload = collection.get(limit=limit, include=["documents", "metadatas"])
    docs: list[dict[str, Any]] = []
    for idx, doc in enumerate(payload.get("documents", []) or []):
        docs.append(
            {
                "document": doc,
                "metadata": (payload.get("metadatas", []) or [{}])[idx] or {},
            }
        )
    return docs


def build_local_context(question: str) -> str:
    classification = classify_question(question)
    parts = [f"question_category={classification.category}"]
    if classification.entities:
        parts.append(f"entities={','.join(classification.entities)}")
    if classification.time_phrases:
        parts.append(f"time_phrases={','.join(classification.time_phrases)}")

    for alias, mapped in FIELD_ALIASES.items():
        if alias in question:
            parts.append(f"alias:{alias}=>{','.join(mapped)}")

    q = question.lower()
    if any(k in question for k in ["订单", "城市", "区域", "客户", "金额"]) or "orders" in q:
        parts.append("orders(order_id, order_date, customer_name, city, region, total_amount)")
    if any(k in question for k in ["商品", "品类", "产品"]) or "products" in q:
        parts.append("products(product_id, product_name, category)")
    if any(k in question for k in ["明细", "数量", "单价", "销量"]) or "order_items" in q:
        parts.append("order_items(order_item_id, order_id, product_id, quantity, unit_price)")
    return "\n".join(parts)


def retrieve_schema_context(question: str, limit: int = 4) -> str:
    """
    检索与问题相关的 schema 上下文。
    
    优先使用向量检索，失败后 fallback 到本地上下文构建 + DDL。
    保持函数签名向后兼容（返回 str）。
    """
    try:
        return get_retriever().retrieve(question, limit)
    except Exception:
        pass

    local_context = build_local_context(question)
    if local_context.strip() and local_context.strip() != "question_category=unknown":
        return local_context

    ddl = load_schema_text()
    return ddl[:1200]
