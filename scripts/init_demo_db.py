from __future__ import annotations

from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "demo_db" / "sales.db"
DDL_PATH = BASE_DIR / "data" / "ddl" / "sales_schema.sql"

SCHEMA = """
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    order_date TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    region TEXT NOT NULL,
    total_amount REAL NOT NULL
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY(order_id) REFERENCES orders(order_id),
    FOREIGN KEY(product_id) REFERENCES products(product_id)
);
""".strip()

PRODUCTS = [
    (1, "云台摄像头", "智能家居"),
    (2, "机械键盘", "数码配件"),
    (3, "人体工学椅", "办公家具"),
    (4, "便携显示器", "数码配件"),
    (5, "降噪耳机", "音频设备"),
    (6, "智能手表", "穿戴设备"),
]

ORDERS = [
    (1001, "2026-01-15", "Alice", "北京", "华北", 2599.00),
    (1002, "2026-01-28", "Bob", "上海", "华东", 1899.00),
    (1003, "2026-02-04", "Cindy", "杭州", "华东", 3299.00),
    (1004, "2026-02-12", "David", "苏州", "华东", 1450.00),
    (1005, "2026-02-18", "Ella", "深圳", "华南", 2199.00),
    (1006, "2026-02-25", "Frank", "上海", "华东", 2799.00),
    (1007, "2026-03-02", "Grace", "北京", "华北", 3099.00),
    (1008, "2026-03-05", "Henry", "广州", "华南", 1688.00),
]

ORDER_ITEMS = [
    (1, 1001, 3, 1, 2599.00),
    (2, 1002, 2, 1, 899.00), (3, 1002, 5, 1, 1000.00),
    (4, 1003, 3, 1, 2599.00), (5, 1003, 6, 1, 700.00),
    (6, 1004, 1, 1, 1450.00),
    (7, 1005, 5, 1, 1199.00), (8, 1005, 2, 1, 1000.00),
    (9, 1006, 4, 1, 1800.00), (10, 1006, 6, 1, 999.00),
    (11, 1007, 3, 1, 3099.00),
    (12, 1008, 1, 1, 888.00), (13, 1008, 2, 1, 800.00),
]


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    cur.executemany("INSERT INTO products(product_id, product_name, category) VALUES (?, ?, ?)", PRODUCTS)
    cur.executemany("INSERT INTO orders(order_id, order_date, customer_name, city, region, total_amount) VALUES (?, ?, ?, ?, ?, ?)", ORDERS)
    cur.executemany("INSERT INTO order_items(order_item_id, order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)", ORDER_ITEMS)
    conn.commit()
    conn.close()
    DDL_PATH.write_text(SCHEMA + "\n", encoding="utf-8")
    print(f"Initialized demo DB at {DB_PATH}")

if __name__ == "__main__":
    main()
