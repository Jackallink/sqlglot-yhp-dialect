#!/usr/bin/env python3
"""
调试子查询中PIVOT语句的解析问题
"""

import sqlglot
from sqlglot import exp
from sqlglot.dialects.yanhuang import Yanhuang

def test_subquery_pivot():
    """测试子查询中的PIVOT语句解析"""
    
    # 测试简单的PIVOT（已知工作）
    sql1 = "PIVOT cities ON country USING SUM(population) GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00') ORDER BY _time"
    
    try:
        parsed = sqlglot.parse_one(sql1, dialect="yanhuang")
        print("✅ 简单PIVOT语法解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 简单PIVOT语法解析失败: {e}")
        print()
    
    # 测试子查询中的PIVOT（问题所在）
    sql2 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00') 
        ORDER BY _time
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql2, dialect="yanhuang")
        print("✅ 子查询PIVOT解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 子查询PIVOT解析失败: {e}")
        print()
    
    # 测试简化的子查询PIVOT
    sql3 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql3, dialect="yanhuang")
        print("✅ 简化子查询PIVOT解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 简化子查询PIVOT解析失败: {e}")
        print()
    
    # 测试带GROUP BY的子查询PIVOT
    sql4 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY _time
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql4, dialect="yanhuang")
        print("✅ 带GROUP BY的子查询PIVOT解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 带GROUP BY的子查询PIVOT解析失败: {e}")
        print()

if __name__ == "__main__":
    print("=== 子查询PIVOT调试 ===\n")
    test_subquery_pivot()
    print("=== 调试完成 ===") 