#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

def test_simple_pivot():
    """测试简单的PIVOT语法"""
    sql = "PIVOT cities ON year USING SUM(population) GROUP BY country"
    
    try:
        parsed = sqlglot.parse_one(sql, dialect=Yanhuang)
        print(f"✅ 简单PIVOT解析成功: {parsed}")
        print(f"生成的SQL: {parsed.sql(dialect=Yanhuang)}")
        
        # 打印解析结果的详细结构
        print(f"解析结果类型: {type(parsed)}")
        print(f"this: {parsed.this}")
        print(f"expressions: {parsed.expressions}")
        print(f"fields: {parsed.fields}")
        print(f"group: {parsed.args.get('group')}")
        
    except Exception as e:
        print(f"❌ 简单PIVOT解析失败: {e}")

def test_pivot_with_order():
    """测试带ORDER BY的PIVOT语法"""
    sql = "PIVOT cities ON year USING SUM(population) GROUP BY country ORDER BY country DESC"
    
    try:
        parsed = sqlglot.parse_one(sql, dialect=Yanhuang)
        print(f"✅ 带ORDER BY的PIVOT解析成功: {parsed}")
        print(f"生成的SQL: {parsed.sql(dialect=Yanhuang)}")
        print(f"解析结果类型: {type(parsed)}")
        
    except Exception as e:
        print(f"❌ 带ORDER BY的PIVOT解析失败: {e}")

def test_pivot_with_in():
    """测试带IN子句的PIVOT语法"""
    sql = "PIVOT cities ON year IN (2000, 2020) USING SUM(population) GROUP BY country"
    
    try:
        parsed = sqlglot.parse_one(sql, dialect=Yanhuang)
        print(f"✅ 带IN子句的PIVOT解析成功: {parsed}")
        print(f"生成的SQL: {parsed.sql(dialect=Yanhuang)}")
        print(f"解析结果类型: {type(parsed)}")
        print(f"fields: {parsed.fields}")
        
    except Exception as e:
        print(f"❌ 带IN子句的PIVOT解析失败: {e}")

def test_pivot_tokens():
    """测试PIVOT相关的token"""
    from sqlglot.tokens import Tokenizer
    from sqlglot.dialects.yanhuang import Yanhuang
    
    tokenizer = Yanhuang.Tokenizer()
    sql = "PIVOT cities ON year IN (2000, 2020) USING SUM(population) GROUP BY country"
    tokens = list(tokenizer.tokenize(sql))
    
    print("Tokens:")
    for i, token in enumerate(tokens):
        print(f"  {i}: {token.token_type} = '{token.text}'")

if __name__ == "__main__":
    print("=== PIVOT调试测试 ===")
    test_pivot_tokens()
    print()
    test_simple_pivot()
    print()
    test_pivot_with_order()
    print()
    test_pivot_with_in() 