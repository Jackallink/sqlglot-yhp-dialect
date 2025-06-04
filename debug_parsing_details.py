#!/usr/bin/env python3
"""
详细调试PIVOT解析过程
"""

import sqlglot
from sqlglot import exp
from sqlglot.dialects.yanhuang import Yanhuang

def test_parsing_details():
    """详细测试解析过程"""
    
    # 测试简单的子查询PIVOT（已知工作）
    sql1 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY _time
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql1, dialect="yanhuang")
        print("✅ 简单子查询PIVOT解析成功!")
        print(f"AST: {parsed}")
        print()
    except Exception as e:
        print(f"❌ 简单子查询PIVOT解析失败: {e}")
        print()
    
    # 测试带ORDER BY的子查询PIVOT（问题所在）
    sql2 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY _time
        ORDER BY _time
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql2, dialect="yanhuang")
        print("✅ 带ORDER BY的子查询PIVOT解析成功!")
        print(f"AST: {parsed}")
        print()
    except Exception as e:
        print(f"❌ 带ORDER BY的子查询PIVOT解析失败: {e}")
        print()
    
    # 测试更简单的ORDER BY
    sql3 = """
    SELECT * FROM (
        PIVOT cities ON country USING SUM(population)
        ORDER BY country
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql3, dialect="yanhuang")
        print("✅ 简单ORDER BY的子查询PIVOT解析成功!")
        print(f"AST: {parsed}")
        print()
    except Exception as e:
        print(f"❌ 简单ORDER BY的子查询PIVOT解析失败: {e}")
        print()

if __name__ == "__main__":
    print("=== 详细解析调试 ===\n")
    test_parsing_details()
    print("=== 调试完成 ===") 