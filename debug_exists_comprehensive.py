#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang
import sqlglot.expressions as exp

def test_exists_scenario(sql, description, expect_error=False):
    print(f"\n=== {description} ===")
    print(f"SQL: {sql}")
    print(f"预期: {'应该报错' if expect_error else '应该成功'}")
    
    try:
        parser = Yanhuang.Parser()
        tokens = Yanhuang.Tokenizer().tokenize(sql)
        ast = parser.parse(tokens, sql)[0]
        print(f"✅ 解析成功: {ast}")
        if expect_error:
            print("❌ 预期报错但实际成功")
        else:
            print("✅ 符合预期")
    except Exception as e:
        print(f"❌ 解析错误: {e}")
        if expect_error:
            print("✅ 符合预期")
        else:
            print("❌ 预期成功但实际报错")

if __name__ == "__main__":
    # 支持的场景：WHERE子句中的非相关EXISTS
    test_exists_scenario(
        "SELECT * FROM orders WHERE EXISTS (SELECT 1 FROM customers)",
        "WHERE子句中的非相关EXISTS子查询",
        expect_error=False
    )
    
    # 不支持的场景1：SELECT子句中的EXISTS  
    test_exists_scenario(
        "SELECT EXISTS (SELECT 1)",
        "SELECT子句中的EXISTS",
        expect_error=True
    )
    
    # 不支持的场景2：相关EXISTS子查询
    test_exists_scenario(
        "SELECT * FROM orders o WHERE EXISTS (SELECT 1 FROM customers c WHERE c.id = o.id)",
        "WHERE子句中的相关EXISTS子查询",
        expect_error=True
    )
    
    # 不支持的场景3：HAVING子句中的EXISTS
    test_exists_scenario(
        "SELECT COUNT(*) FROM orders GROUP BY CustomerID HAVING EXISTS (SELECT 1 FROM customers WHERE CustomerID = orders.CustomerID)",
        "HAVING子句中的EXISTS",
        expect_error=True
    )
    
    # 不支持的场景4：ORDER BY子句中的EXISTS
    test_exists_scenario(
        "SELECT * FROM orders ORDER BY EXISTS (SELECT 1 FROM customers WHERE CustomerID = orders.CustomerID)",
        "ORDER BY子句中的EXISTS",
        expect_error=True
    )
    
    # 支持的场景：复杂WHERE条件中的非相关EXISTS
    test_exists_scenario(
        "SELECT * FROM orders WHERE a = 1 AND EXISTS (SELECT 1 FROM customers) OR b = 2",
        "复杂WHERE条件中的非相关EXISTS",
        expect_error=False
    ) 