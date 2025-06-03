#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang
import sqlglot.expressions as exp

def debug_correlated_sql(sql, description):
    print(f"\n=== {description} ===")
    print(f"SQL: {sql}")
    try:
        # 直接使用yanhuang方言解析，应该触发我们的检测逻辑
        parser = Yanhuang.Parser()
        tokens = Yanhuang.Tokenizer().tokenize(sql)
        ast = parser.parse(tokens, sql)[0]
        print(f"Parse success: {ast}")
    except Exception as e:
        print(f"Parse error (expected for correlated): {e}")

# 测试用例 - 先测试非相关的，确保正常解析
debug_correlated_sql(
    "SELECT * FROM orders WHERE CustomerID IN (SELECT CustomerID FROM customers)",
    "非相关IN子查询"
)

debug_correlated_sql(
    "SELECT * FROM orders WHERE EXISTS (SELECT 1 FROM customers)",
    "非相关EXISTS子查询"
)

# 再测试相关的，应该抛出错误
debug_correlated_sql(
    "SELECT * FROM orders o WHERE o.CustomerID IN (SELECT c.CustomerID FROM customers c WHERE c.Region = o.Region)",
    "相关IN子查询"
)

debug_correlated_sql(
    "SELECT * FROM orders o WHERE EXISTS (SELECT 1 FROM customers c WHERE c.id = o.id)",
    "相关EXISTS子查询"
) 