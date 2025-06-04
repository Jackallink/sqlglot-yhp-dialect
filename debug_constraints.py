#!/usr/bin/env python3
"""
调试约束问题
"""

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang
from sqlglot import exp, parse_one
import traceback

def debug_constraint_parsing():
    """调试约束解析"""
    test_cases = [
        ("PRIMARY KEY约束", "CREATE TABLE test (id INT PRIMARY KEY, name VARCHAR(100))"),
        ("FOREIGN KEY约束", "CREATE TABLE test (id INT REFERENCES other_table(id))"),
        ("UNIQUE约束", "CREATE TABLE test (id INT UNIQUE, name VARCHAR(100))"),
        ("CHECK约束", "CREATE TABLE test (id INT CHECK (id > 0), name VARCHAR(100))"),
        ("复杂类型BYTEA", "SELECT decode('abc', 'hex')::BYTEA as data"),
    ]
    
    for name, sql in test_cases:
        print(f"\n=== {name} ===")
        print(f"SQL: {sql}")
        
        try:
            parsed = parse_one(sql, dialect=Yanhuang)
            print(f"解析成功: {type(parsed)}")
            
            # 详细分析AST结构
            if isinstance(parsed, exp.Create):
                print(f"CREATE语句args: {parsed.args}")
                
                # 查找this字段（表名）
                table_name = parsed.args.get("this")
                print(f"表名: {table_name}")
                
                # 查找schema字段
                schema = parsed.args.get("this")  # 在CREATE中，this通常包含schema
                if hasattr(parsed, 'this') and isinstance(parsed.this, exp.Schema):
                    schema = parsed.this
                    print(f"Schema类型: {type(schema)}")
                    print(f"Schema表达式数量: {len(schema.expressions) if hasattr(schema, 'expressions') else 0}")
                    
                    if hasattr(schema, 'expressions'):
                        for i, expr in enumerate(schema.expressions):
                            print(f"  Expression {i}: {type(expr)} - {expr}")
                            if isinstance(expr, exp.ColumnDef):
                                constraints = expr.args.get("constraints", [])
                                print(f"    约束数量: {len(constraints)}")
                                for j, constraint in enumerate(constraints):
                                    print(f"      约束 {j}: {type(constraint)} - {constraint}")
                                    if isinstance(constraint, exp.ColumnConstraint):
                                        kind = constraint.args.get("kind")
                                        print(f"        约束种类: {type(kind)} - {kind}")
                                    if hasattr(constraint, 'args'):
                                        print(f"        约束args: {constraint.args}")
                else:
                    # 尝试获取解析器内部结构
                    print("未找到schema，尝试查看完整AST:")
                    def traverse_ast(node, level=0):
                        indent = "  " * level
                        print(f"{indent}{type(node).__name__}: {str(node)[:100]}")
                        if hasattr(node, 'args') and node.args:
                            for key, value in node.args.items():
                                print(f"{indent}  {key}: {type(value)} - {str(value)[:50]}")
                                if isinstance(value, exp.Expression):
                                    traverse_ast(value, level + 2)
                                elif isinstance(value, list):
                                    for i, item in enumerate(value):
                                        if isinstance(item, exp.Expression):
                                            print(f"{indent}    [{i}]:")
                                            traverse_ast(item, level + 3)
                    
                    traverse_ast(parsed)
                    
            elif isinstance(parsed, exp.Select):
                # 分析SELECT语句中的表达式
                for expr in parsed.expressions:
                    print(f"  表达式: {type(expr)} - {expr}")
                    if isinstance(expr, exp.Alias):
                        this = expr.this
                        print(f"    别名表达式: {type(this)} - {this}")
                        # 检查是否是Cast表达式
                        if isinstance(this, exp.Cast):
                            to_type = this.args.get('to')
                            print(f"    转换目标类型: {type(to_type)} - {to_type}")
                            if isinstance(to_type, exp.DataType):
                                print(f"    数据类型: {to_type.this}")
                                print(f"    数据类型值: {to_type.this.value}")
            
        except Exception as e:
            print(f"解析错误: {e}")
            print(f"错误类型: {type(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    debug_constraint_parsing() 