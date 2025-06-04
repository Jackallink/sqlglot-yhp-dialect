#!/usr/bin/env python3
"""
调试TIME()函数在子查询PIVOT中的解析问题
"""

import sqlglot
from sqlglot import exp
from sqlglot.dialects.yanhuang import Yanhuang

def test_time_function_in_subquery():
    """测试TIME()函数在子查询PIVOT中的解析"""
    
    # 测试简单的TIME()函数（已知工作）
    sql1 = "PIVOT cities ON country USING SUM(population) GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00')"
    
    try:
        parsed = sqlglot.parse_one(sql1, dialect="yanhuang")
        print("✅ 简单TIME()函数PIVOT解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 简单TIME()函数PIVOT解析失败: {e}")
        print()
    
    # 测试子查询中的TIME()函数（问题所在）
    sql2 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00')
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql2, dialect="yanhuang")
        print("✅ 子查询TIME()函数PIVOT解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 子查询TIME()函数PIVOT解析失败: {e}")
        print()
    
    # 测试子查询中的普通函数
    sql3 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY UPPER(country)
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql3, dialect="yanhuang")
        print("✅ 子查询普通函数PIVOT解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 子查询普通函数PIVOT解析失败: {e}")
        print()
    
    # 测试子查询中的TIME()函数但不带参数
    sql4 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY TIME()
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql4, dialect="yanhuang")
        print("✅ 子查询TIME()无参数PIVOT解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 子查询TIME()无参数PIVOT解析失败: {e}")
        print()

if __name__ == "__main__":
    print("=== TIME()函数子查询调试 ===\n")
    test_time_function_in_subquery()
    print("=== 调试完成 ===") 