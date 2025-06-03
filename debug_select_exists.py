#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang
import sqlglot.expressions as exp

def debug_select_exists():
    sql = "SELECT EXISTS (SELECT 1)"
    print(f"SQL: {sql}")
    
    try:
        # 使用yanhuang方言解析
        parser = Yanhuang.Parser()
        tokens = Yanhuang.Tokenizer().tokenize(sql)
        ast = parser.parse(tokens, sql)[0]
        print(f"Parse success: {ast}")
        
        # 分析AST结构
        print(f"AST type: {type(ast)}")
        if hasattr(ast, 'expressions'):
            print(f"Expressions: {ast.expressions}")
            for i, expr in enumerate(ast.expressions):
                print(f"  Expression {i}: {expr} (type: {type(expr)})")
                # 检查是否是EXISTS
                if isinstance(expr, exp.Exists):
                    print(f"    Found EXISTS in SELECT clause!")
                # 检查是否EXISTS在表达式内部
                for exists in expr.find_all(exp.Exists):
                    print(f"    Found nested EXISTS: {exists}")
                    
    except Exception as e:
        print(f"Parse error: {e}")

if __name__ == "__main__":
    debug_select_exists() 