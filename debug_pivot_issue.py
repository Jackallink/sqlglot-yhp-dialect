#!/usr/bin/env python3
"""
调试PIVOT ORDER BY解析问题
"""

import sqlglot
from sqlglot import tokens
from sqlglot.dialects.yanhuang import Yanhuang

def debug_tokenization():
    """调试分词"""
    sql = "PIVOT cities ON year USING SUM(population) GROUP BY country ORDER BY country DESC"
    
    print("=== 分词调试 ===")
    print(f"SQL: {sql}")
    
    tokenizer = Yanhuang.Tokenizer()
    tokens_list = list(tokenizer.tokenize(sql))
    
    print("Tokens:")
    for i, token in enumerate(tokens_list):
        if i >= 10:  # 重点看后面的token
            print(f"  {i:2d}: {token.token_type:<20} = '{token.text}'")
    print()

def debug_simple_pivot():
    """测试简单PIVOT"""
    sql = "PIVOT cities ON year USING SUM(population)"
    print(f"测试简单PIVOT: {sql}")
    try:
        parsed = sqlglot.parse_one(sql, dialect='yanhuang')
        print(f"✅ 成功: {parsed}")
    except Exception as e:
        print(f"❌ 失败: {e}")
    print()

def debug_pivot_with_group():
    """测试带GROUP BY的PIVOT"""
    sql = "PIVOT cities ON year USING SUM(population) GROUP BY country"
    print(f"测试带GROUP BY的PIVOT: {sql}")
    try:
        parsed = sqlglot.parse_one(sql, dialect='yanhuang')
        print(f"✅ 成功: {parsed}")
    except Exception as e:
        print(f"❌ 失败: {e}")
    print()

def debug_pivot_with_order():
    """测试带ORDER BY的PIVOT"""
    sql = "PIVOT cities ON year USING SUM(population) ORDER BY country"
    print(f"测试带ORDER BY的PIVOT: {sql}")
    try:
        parsed = sqlglot.parse_one(sql, dialect='yanhuang')
        print(f"✅ 成功: {parsed}")
    except Exception as e:
        print(f"❌ 失败: {e}")
    print()

def debug_full_pivot():
    """测试完整PIVOT"""
    sql = "PIVOT cities ON year USING SUM(population) GROUP BY country ORDER BY country DESC"
    print(f"测试完整PIVOT: {sql}")
    try:
        parsed = sqlglot.parse_one(sql, dialect='yanhuang')
        print(f"✅ 成功: {parsed}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    print()

if __name__ == "__main__":
    debug_tokenization()
    debug_simple_pivot()
    debug_pivot_with_group()
    debug_pivot_with_order()
    debug_full_pivot() 