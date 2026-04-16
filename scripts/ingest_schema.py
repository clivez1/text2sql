from __future__ import annotations

from pathlib import Path

import chromadb

from app.config.settings import get_settings

BASE_DIR = Path(__file__).resolve().parents[1]
DDL_PATH = BASE_DIR / "data" / "ddl" / "sales_schema.sql"

FIELD_DOCS = {
    "orders": "表 orders：订单主表。字段含义：order_id 订单ID，order_date 下单日期，customer_name 客户名，city 城市，region 区域，total_amount 订单总金额。常见单表问题：订单总数、各城市订单量、区域销售额、最近订单列表。",
    "products": "表 products：商品维表。字段含义：product_id 商品ID，product_name 商品名，category 商品类别。常见单表问题：商品总数、按类别统计商品数、筛选某个类别商品列表。",
    "order_items": "表 order_items：订单明细表。字段含义：order_item_id 明细ID，order_id 订单ID，product_id 商品ID，quantity 购买数量，unit_price 成交单价。常见单表问题：明细总数、平均购买数量、最高/最低单价、按 product_id 统计销量。",
}

EXAMPLE_SQL = {
    "orders_example": "SELECT city, COUNT(*) AS order_count FROM orders GROUP BY city ORDER BY order_count DESC LIMIT 10;",
    "products_example": "SELECT category, COUNT(*) AS product_count FROM products GROUP BY category ORDER BY product_count DESC LIMIT 20;",
    "order_items_example": "SELECT product_id, SUM(quantity) AS total_quantity FROM order_items GROUP BY product_id ORDER BY total_quantity DESC LIMIT 20;",
}


def main() -> None:
    settings = get_settings()
    settings_path = Path(settings.vector_db_path) / "schema_store"
    settings_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(settings_path))
    try:
        client.delete_collection("schema_docs")
    except Exception:
        pass
    collection = client.create_collection("schema_docs")

    documents = []
    metadatas = []
    ids = []

    ddl_text = DDL_PATH.read_text(encoding="utf-8")
    documents.append(f"DDL 全量定义：\n{ddl_text}")
    metadatas.append({"type": "ddl", "name": "sales_schema"})
    ids.append("ddl_sales_schema")

    for table_name, doc in FIELD_DOCS.items():
        documents.append(doc)
        metadatas.append({"type": "field_doc", "table": table_name})
        ids.append(f"field_doc_{table_name}")

    for key, sql in EXAMPLE_SQL.items():
        documents.append(f"示例 SQL：{sql}")
        metadatas.append({"type": "example_sql", "name": key})
        ids.append(key)

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Ingested {len(ids)} schema/example documents into {settings_path}")


if __name__ == "__main__":
    main()
