#!/usr/bin/env python3
"""
调试PIVOT解析问题
"""

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang
from sqlglot import tokens

def debug_tokenization():
    """调试分词过程"""
    sql = "PIVOT cities ON year USING SUM(population) GROUP BY country"
    
    print("=== 分词调试 ===")
    print(f"SQL: {sql}")
    
    # 使用炎凰方言的分词器
    tokenizer = Yanhuang.Tokenizer()
    tokens_list = list(tokenizer.tokenize(sql))
    
    print("Tokens:")
    for i, token in enumerate(tokens_list):
        print(f"  {i}: {token}")
    
    print()

def debug_parsing():
    """调试解析过程"""
    sql = "PIVOT cities ON year USING SUM(population) GROUP BY country"
    
    print("=== 解析调试 ===")
    print(f"SQL: {sql}")
    
    try:
        # 使用炎凰方言的解析器
        parser = Yanhuang.Parser()
        parsed = parser.parse(sql)
        print(f"解析结果: {parsed}")
        
        if parsed:
            for stmt in parsed:
                print(f"语句类型: {type(stmt)}")
                print(f"语句内容: {stmt}")
        
    except Exception as e:
        print(f"解析错误: {e}")
        import traceback
        traceback.print_exc()
    
    print()

def debug_simple_pivot():
    """调试简单的PIVOT语句"""
    sql = "PIVOT cities ON year USING SUM(population)"
    
    print("=== 简单PIVOT调试 ===")
    print(f"SQL: {sql}")
    
    try:
        parsed = sqlglot.parse_one(sql, dialect="yanhuang")
        print(f"解析成功: {parsed}")
        print(f"类型: {type(parsed)}")
        print(f"重新生成SQL: {parsed.sql(dialect='yanhuang')}")
    except Exception as e:
        print(f"解析失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()

if __name__ == "__main__":
    debug_tokenization()
    debug_parsing()
    debug_simple_pivot() 