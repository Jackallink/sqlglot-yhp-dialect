#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

def test_sql(sql, expect_success=True):
    print(f"\nSQL: {sql}")
    print(f"预期: {'成功' if expect_success else '失败'}")
    
    try:
        parser = Yanhuang.Parser()
        tokens = Yanhuang.Tokenizer().tokenize(sql)
        ast = parser.parse(tokens, sql)[0]
        print(f"✅ 解析成功")
        return expect_success
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        return not expect_success

if __name__ == "__main__":
    print("=== 炎凰SQL EXISTS功能验证 ===")
    
    # 文档示例1：支持的WHERE EXISTS
    success_count = 0
    total_count = 0
    
    total_count += 1
    if test_sql("""SELECT * FROM orders WHERE EXISTS (
       SELECT CustomerID 
       FROM customers
       )""", expect_success=True):
        success_count += 1
    
    # 文档示例2：不支持的相关子查询
    total_count += 1
    if test_sql("""SELECT CustomerID FROM orders AS outside WHERE EXISTS(
         SELECT CustomerID
         FROM customers AS inside
         WHERE inside.CustomerID = outside.CustomerID
         )""", expect_success=False):
        success_count += 1
    
    # 文档示例3：不支持的SELECT EXISTS
    total_count += 1
    if test_sql("SELECT EXISTS (SELECT 1)", expect_success=False):
        success_count += 1
    
    # 额外验证：WHERE中非相关EXISTS变体
    total_count += 1
    if test_sql("SELECT * FROM orders WHERE NOT EXISTS (SELECT 1 FROM customers)", expect_success=True):
        success_count += 1
    
    # 额外验证：HAVING中的EXISTS
    total_count += 1  
    if test_sql("SELECT COUNT(*) FROM orders GROUP BY CustomerID HAVING EXISTS (SELECT 1 FROM customers)", expect_success=False):
        success_count += 1
        
    print(f"\n=== 结果总结 ===")
    print(f"测试通过: {success_count}/{total_count}")
    if success_count == total_count:
        print("🎉 所有测试通过！EXISTS功能完全符合文档要求。")
    else:
        print("❌ 部分测试失败，需要进一步检查。") 