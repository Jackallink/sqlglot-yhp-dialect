#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

def debug_window_issue():
    """调试WINDOW子句解析问题"""
    
    sql = "SELECT COUNT(*) OVER w FROM main WINDOW w AS (PARTITION BY id)"
    print(f"SQL: {sql}")
    
    # 1. 先用PostgreSQL方言测试
    print("\n=== PostgreSQL方言 ===")
    pg_ast = sqlglot.parse_one(sql, dialect='postgres')
    print(f"PG AST: {pg_ast}")
    print(f"PG Windows: {pg_ast.args.get('windows', 'None')}")
    
    # 2. 再用炎凰方言测试
    print("\n=== 炎凰SQL方言 ===")
    try:
        yh_ast = sqlglot.parse_one(sql, dialect='yanhuang')
        print(f"YH AST: {yh_ast}")
        print(f"YH Windows: {yh_ast.args.get('windows', 'None')}")
    except Exception as e:
        print(f"炎凰方言解析错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 测试炎凰方言是否调用了我们的转换方法
    print("\n=== 炎凰解析流程调试 ===")
    try:
        parser = Yanhuang.Parser()
        tokenizer = Yanhuang.Tokenizer()
        tokens = tokenizer.tokenize(sql)
        
        # 手动设置tokens
        parser.tokens = tokens
        parser.index = 0
        parser._curr = tokens[0] if tokens else None
        parser._prev = None
        parser._next = tokens[1] if len(tokens) > 1 else None
        
        # 调用我们重写的_parse_statement
        statement = parser._parse_statement()
        print(f"解析后的statement: {statement}")
        print(f"Windows: {statement.args.get('windows', 'None') if statement else 'None'}")
        
    except Exception as e:
        print(f"手动解析错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_window_issue() 