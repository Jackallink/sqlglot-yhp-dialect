#!/usr/bin/env python3
"""
调试炎凰SQL的EXCEPT语法解析问题
"""

import sqlglot
from sqlglot import exp
from sqlglot.dialects.yanhuang import Yanhuang

def test_except_syntax():
    """测试EXCEPT语法解析"""
    
    # 测试简单的EXCEPT语法
    sql1 = 'SELECT * EXCEPT ("NULL") FROM cities'
    
    try:
        parsed = sqlglot.parse_one(sql1, dialect="yanhuang")
        print("✅ 简单EXCEPT语法解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 简单EXCEPT语法解析失败: {e}")
        print()
    
    # 测试复杂的嵌套查询
    sql2 = """
    SELECT * EXCEPT ("NULL") FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00') 
        ORDER BY _time
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql2, dialect="yanhuang")
        print("✅ 复杂EXCEPT查询解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 复杂EXCEPT查询解析失败: {e}")
        print()
    
    # 测试不带EXCEPT的相同查询
    sql3 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00') 
        ORDER BY _time
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql3, dialect="yanhuang")
        print("✅ 不带EXCEPT的查询解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 不带EXCEPT的查询解析失败: {e}")
        print()

if __name__ == "__main__":
    print("=== 炎凰SQL EXCEPT语法调试 ===\n")
    test_except_syntax()
    print("=== 调试完成 ===") 