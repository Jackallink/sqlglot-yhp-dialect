#!/usr/bin/env python3
"""
简单的ROLLUP测试脚本
"""

import warnings
import sqlglot
from sqlglot.dialects import yanhuang

def test_rollup():
    sql = "SELECT a, b, SUM(c) FROM t GROUP BY ROLLUP(a, b)"
    print(f"测试SQL: {sql}")
    print(f"使用的方言文件: {yanhuang.__file__}")
    
    # 捕获警告
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # 使用 transpile
        result = sqlglot.transpile(sql, read="postgres", write="yanhuang")[0]
        
        print(f"转换结果: {result}")
        print(f"警告数量: {len(w)}")
        for warning in w:
            print(f"  警告: {warning.message}")
    
    # 直接解析并查看AST
    print("\n=== AST分析 ===")
    parsed = sqlglot.parse_one(sql, read="postgres")
    
    # 查找Group表达式
    for node in parsed.walk():
        if isinstance(node, sqlglot.expressions.Group):
            print(f"Group: {node}")
            print(f"Group.args: {node.args}")
            print(f"rollup属性: {node.args.get('rollup')}")
            break

if __name__ == "__main__":
    test_rollup() 