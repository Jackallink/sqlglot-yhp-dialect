#!/usr/bin/env python3
"""
调试原始失败的查询
"""

import sqlglot
from sqlglot import exp
from sqlglot.dialects.yanhuang import Yanhuang

def test_original_issue():
    """测试原始失败的查询"""
    
    # 原始失败的查询
    sql1 = """
    SELECT * EXCEPT ("NULL") FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00') 
        ORDER BY _time
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql1, dialect="yanhuang")
        print("✅ 原始查询解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 原始查询解析失败: {e}")
        print()
    
    # 测试不带ORDER BY的版本
    sql2 = """
    SELECT * EXCEPT ("NULL") FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00')
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql2, dialect="yanhuang")
        print("✅ 不带ORDER BY的查询解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 不带ORDER BY的查询解析失败: {e}")
        print()
    
    # 测试带ORDER BY但不带EXCEPT的版本
    sql3 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00') 
        ORDER BY _time
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql3, dialect="yanhuang")
        print("✅ 带ORDER BY不带EXCEPT的查询解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 带ORDER BY不带EXCEPT的查询解析失败: {e}")
        print()

if __name__ == "__main__":
    print("=== 原始问题调试 ===\n")
    test_original_issue()
    print("=== 调试完成 ===") 