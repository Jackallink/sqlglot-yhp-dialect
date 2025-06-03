#!/usr/bin/env python3

import sqlglot.expressions as exp

def debug_exists_detection():
    sql = "SELECT * FROM orders o WHERE EXISTS (SELECT 1 FROM customers c WHERE c.id = o.id)"
    print(f"SQL: {sql}")
    
    # 使用标准sqlglot解析查看AST结构
    ast = sqlglot.parse_one(sql, dialect="yanhuang")
    print(f"AST: {ast}")
    
    # 查找EXISTS
    for exists in ast.find_all(exp.Exists):
        print(f"Found EXISTS: {exists}")
        subquery = exists.this
        print(f"Subquery: {subquery}")
        print(f"Subquery type: {type(subquery)}")
        
        # 查找子查询中的所有列
        for col in subquery.find_all(exp.Column):
            print(f"  Column: {col}")
            print(f"    Table: {col.table}")
            if col.table:
                table_name = str(col.table).lower()
                print(f"    Table name: '{table_name}', length: {len(table_name)}")
                print(f"    Is single char?: {len(table_name) == 1}")
                print(f"    In allowed list?: {table_name in ['o', 'c', 't', 'a', 'b']}")
                if len(table_name) == 1 and table_name in ['o', 'c', 't', 'a', 'b']:
                    print(f"    *** SHOULD TRIGGER ERROR for table '{table_name}' ***")

if __name__ == "__main__":
    import sqlglot
    debug_exists_detection() 