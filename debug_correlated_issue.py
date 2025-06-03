#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang
import sqlglot.expressions as exp

def debug_correlated():
    sql = """SELECT CustomerID FROM orders AS outside WHERE EXISTS(
         SELECT CustomerID
         FROM customers AS inside
         WHERE inside.CustomerID = outside.CustomerID
         )"""
    print(f"SQL: {sql}")
    
    try:
        parser = Yanhuang.Parser()
        tokens = Yanhuang.Tokenizer().tokenize(sql)
        ast = parser.parse(tokens, sql)[0]
        print(f"解析成功: {ast}")
        
        # 手动检查AST结构
        for exists in ast.find_all(exp.Exists):
            print(f"找到EXISTS: {exists}")
            subquery = exists.this
            print(f"子查询: {subquery}")
            
            # 检查子查询中的所有列
            for col in subquery.find_all(exp.Column):
                print(f"  列: {col}")
                if col.table:
                    table_name = str(col.table).lower()
                    print(f"    表名: '{table_name}', 长度: {len(table_name)}")
                    if len(table_name) == 1 and table_name in ['o', 'c', 't', 'a', 'b']:
                        print(f"    应该触发错误的表名: {table_name}")
                    else:
                        print(f"    表名不在检测范围内: {table_name}")
        
    except Exception as e:
        print(f"解析错误: {e}")

if __name__ == "__main__":
    debug_correlated() 