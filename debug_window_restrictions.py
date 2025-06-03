#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang
import sqlglot.expressions as exp

def test_window_restrictions():
    """调试窗口函数限制"""
    
    test_cases = [
        # 1. ORDER BY中使用窗口函数
        "SELECT * FROM main ORDER BY COUNT(*) OVER (PARTITION BY id)",
        
        # 2. 窗口函数运算
        "SELECT (COUNT(*) OVER ()) + 1 FROM main",
        
        # 3. WINDOW子句
        "SELECT COUNT(*) OVER w FROM main WINDOW w AS (PARTITION BY id)",
        
        # 4. RANGE框架
        "SELECT SUM(size) OVER (ORDER BY time RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main"
    ]
    
    for i, sql in enumerate(test_cases, 1):
        print(f"\n=== 测试 {i}: {sql} ===")
        
        try:
            parser = Yanhuang.Parser()
            tokens = Yanhuang.Tokenizer().tokenize(sql)
            ast = parser.parse(tokens, sql)[0]
            
            print(f"解析成功，AST: {ast}")
            print("❌ 预期应该报错但实际成功")
            
            # 分析AST结构
            if isinstance(ast, exp.Select):
                print(f"ORDER BY: {ast.args.get('order')}")
                print(f"WINDOW: {ast.args.get('window')}")
                print(f"表达式: {ast.expressions}")
                
                # 手动检查
                if ast.args.get("order"):
                    print("检查ORDER BY中的窗口函数...")
                    for order_expr in ast.args["order"].find_all(exp.Window):
                        print(f"  发现ORDER BY中的窗口函数: {order_expr}")
                
                # 检查表达式中的运算
                for expr in ast.expressions:
                    print(f"  检查表达式: {expr} (类型: {type(expr)})")
                    if isinstance(expr, exp.Binary):
                        print(f"    二元运算: left={expr.this} (类型: {type(expr.this)}), right={expr.expression} (类型: {type(expr.expression)})")
                        
        except Exception as e:
            print(f"✅ 正确报错: {e}")

if __name__ == "__main__":
    test_window_restrictions() 