#!/usr/bin/env python3
"""
测试炎凰SQL的PIVOT透视转换功能实现
"""

import sqlglot
from sqlglot import exp
from sqlglot.dialects.yanhuang import Yanhuang

def test_pivot_parsing():
    """测试PIVOT语法解析"""
    
    # 测试基本PIVOT语法
    sql1 = "PIVOT cities ON year USING SUM(population) GROUP BY country ORDER BY country DESC"
    
    try:
        parsed = sqlglot.parse_one(sql1, dialect="yanhuang")
        print("✅ 基本PIVOT语法解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 基本PIVOT语法解析失败: {e}")
        print()
    
    # 测试带IN子句的PIVOT语法
    sql2 = "PIVOT cities ON year IN (2000, 2020) USING SUM(population) GROUP BY country ORDER BY country DESC"
    
    try:
        parsed = sqlglot.parse_one(sql2, dialect="yanhuang")
        print("✅ 带IN子句PIVOT语法解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 带IN子句PIVOT语法解析失败: {e}")
        print()
    
    # 测试复杂聚合表达式
    sql3 = "PIVOT cities ON year USING SUM(population)+1 GROUP BY country ORDER BY country DESC"
    
    try:
        parsed = sqlglot.parse_one(sql3, dialect="yanhuang")
        print("✅ 复杂聚合表达式PIVOT语法解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 复杂聚合表达式PIVOT语法解析失败: {e}")
        print()
    
    # 测试结合GROUP BY TIME()的PIVOT
    sql4 = "PIVOT cities ON country USING SUM(population) GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00') ORDER BY _time"
    
    try:
        parsed = sqlglot.parse_one(sql4, dialect="yanhuang")
        print("✅ 结合TIME()的PIVOT语法解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 结合TIME()的PIVOT语法解析失败: {e}")
        print()

def test_pivot_in_select():
    """测试在SELECT语句中使用PIVOT"""
    
    # 测试复杂的PIVOT查询
    sql = """
    SELECT * EXCEPT ("NULL") FROM (
        PIVOT cities ON country USING SUM(population)
        GROUP BY TIME(span='5y', start='1990-01-01T00:00:00', end='2020-01-01T00:00:00') 
        ORDER BY _time
    )
    """
    
    try:
        parsed = sqlglot.parse_one(sql, dialect="yanhuang")
        print("✅ 复杂PIVOT查询解析成功!")
        print(f"AST: {parsed}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
        print()
    except Exception as e:
        print(f"❌ 复杂PIVOT查询解析失败: {e}")
        print()

if __name__ == "__main__":
    print("=== 炎凰SQL PIVOT功能测试 ===\n")
    
    test_pivot_parsing()
    test_pivot_in_select()
    
    print("=== 测试完成 ===") 