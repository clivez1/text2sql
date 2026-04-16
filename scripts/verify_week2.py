#!/usr/bin/env python
"""
Week 2 验证脚本
测试数据库抽象层和安全校验功能
"""
from __future__ import annotations

import sys
from pathlib import Path

# 添加项目根目录到 path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.sql.database import create_database_connector, SQLiteConnector, MySQLConnector
from app.core.sql.guard import SQLValidator, validate_readonly_sql
from app.core.sql.executor import get_executor, run_query


def test_database_abstraction():
    """测试数据库抽象层"""
    print("=" * 50)
    print("测试 1: 数据库抽象层")
    print("=" * 50)
    
    # 测试 SQLite 连接器
    print("\n1.1 SQLite 连接器测试:")
    try:
        connector = create_database_connector()
        success, msg = connector.test_connection()
        print(f"   连接测试: {'✅' if success else '❌'} {msg}")
        
        if success:
            schema = connector.get_schema_info()
            print(f"   Schema 信息: {len(schema)} 字符")
            print(f"   表列表: {connector.execute_query('SELECT name FROM sqlite_master WHERE type=\"table\"')['name'].tolist()}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    print("\n✅ 数据库抽象层测试完成")


def test_sql_validation():
    """测试 SQL 安全校验"""
    print("\n" + "=" * 50)
    print("测试 2: SQL 安全校验")
    print("=" * 50)
    
    validator = SQLValidator()
    
    # 测试用例
    test_cases = [
        # (SQL, 应该通过, 描述)
        ("SELECT * FROM orders LIMIT 10", True, "正常 SELECT"),
        ("SELECT * FROM orders", True, "无 LIMIT 的 SELECT（自动添加）"),
        ("INSERT INTO orders VALUES (1)", False, "INSERT 语句"),
        ("DELETE FROM orders", False, "DELETE 语句"),
        ("DROP TABLE orders", False, "DROP 语句"),
        ("SELECT * FROM forbidden_table", False, "未授权表"),
        ("SELECT password FROM users", True, "包含敏感字段（警告但不阻止）"),
        ("SELECT * FROM orders; DROP TABLE orders;", False, "多语句攻击"),
        ("SELECT * FROM orders WHERE id = 1 OR 1=1", True, "简单注入尝试（语法正确）"),
    ]
    
    passed = 0
    failed = 0
    
    for sql, should_pass, desc in test_cases:
        result = validator.validate(sql)
        if result.is_valid == should_pass:
            print(f"   ✅ {desc}")
            passed += 1
        else:
            print(f"   ❌ {desc}: 预期 {should_pass}, 实际 {result.is_valid}")
            if result.error:
                print(f"      错误: {result.error}")
            failed += 1
    
    print(f"\n   结果: {passed} 通过, {failed} 失败")
    print("\n✅ SQL 安全校验测试完成")


def test_query_executor():
    """测试查询执行器"""
    print("\n" + "=" * 50)
    print("测试 3: 查询执行器")
    print("=" * 50)
    
    executor = get_executor()
    
    # 测试连接
    print("\n3.1 连接测试:")
    success, msg = executor.test_connection()
    print(f"   {'✅' if success else '❌'} {msg}")
    
    # 测试查询
    print("\n3.2 查询测试:")
    test_queries = [
        "SELECT COUNT(*) as count FROM orders",
        "SELECT * FROM products LIMIT 5",
        "SELECT city, COUNT(*) as cnt FROM orders GROUP BY city ORDER BY cnt DESC LIMIT 5",
    ]
    
    for sql in test_queries:
        try:
            df = executor.execute(sql)
            print(f"   ✅ {sql[:50]}... -> {len(df)} 行")
        except Exception as e:
            print(f"   ❌ {sql[:50]}... -> {e}")
    
    print("\n✅ 查询执行器测试完成")


def test_integration():
    """集成测试：完整链路"""
    print("\n" + "=" * 50)
    print("测试 4: 集成测试")
    print("=" * 50)
    
    # 使用原有接口测试向后兼容
    print("\n4.1 向后兼容测试 (run_query):")
    try:
        df = run_query("SELECT * FROM orders LIMIT 3")
        print(f"   ✅ run_query 返回 {len(df)} 行")
        print(f"   列: {list(df.columns)}")
    except Exception as e:
        print(f"   ❌ run_query 失败: {e}")
    
    print("\n✅ 集成测试完成")


def main():
    print("\n" + "=" * 60)
    print("       Text2SQL Agent - Week 2 验证测试")
    print("=" * 60)
    
    test_database_abstraction()
    test_sql_validation()
    test_query_executor()
    test_integration()
    
    print("\n" + "=" * 60)
    print("       Week 2 验证测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()