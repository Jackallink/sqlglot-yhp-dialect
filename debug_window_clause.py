#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang
import sqlglot.expressions as exp

def debug_window_clause():
    """调试WINDOW子句的解析"""
    
    sql = "SELECT COUNT(*) OVER w FROM main WINDOW w AS (PARTITION BY id)"
    print(f"SQL: {sql}")
    
    try:
        # 使用标准postgres方言解析，看看AST结构
        print("\n=== 使用Postgres方言解析 ===")
        pg_parser = sqlglot.dialects.postgres.Postgres.Parser()
        pg_tokens = sqlglot.dialects.postgres.Postgres.Tokenizer().tokenize(sql)
        pg_ast = pg_parser.parse(pg_tokens, sql)[0]
        print(f"PG AST: {pg_ast}")
        print(f"PG WINDOW: {pg_ast.args.get('window')}")
        
        # 查找所有属性
        print("\n=== PG AST 属性 ===")
        for key, value in pg_ast.args.items():
            print(f"  {key}: {value}")
            
        print("\n=== 使用炎凰方言解析 ===")
        yh_parser = Yanhuang.Parser()
        yh_tokens = Yanhuang.Tokenizer().tokenize(sql)
        yh_ast = yh_parser.parse(yh_tokens, sql)[0]
        print(f"YH AST: {yh_ast}")
        print(f"YH WINDOW: {yh_ast.args.get('window')}")
        
        # 查找所有属性
        print("\n=== YH AST 属性 ===")
        for key, value in yh_ast.args.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    debug_window_clause() 