#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

def test_basic_keywords():
    """测试基础SQL关键词的实现状态"""
    
    test_cases = [
        # ORDER BY 测试
        ("ORDER BY基础", "SELECT * FROM main ORDER BY a"),
        ("ORDER BY ASC/DESC", "SELECT * FROM main ORDER BY a ASC, b DESC"),
        ("ORDER BY表达式", "SELECT * FROM main ORDER BY CAST(size AS INT) DESC"),
        
        # GROUP BY 测试
        ("GROUP BY基础", "SELECT COUNT(*) FROM main GROUP BY method"),
        ("GROUP BY多字段", "SELECT COUNT(*) FROM main GROUP BY method, agent"),
        ("GROUP BY + HAVING", "SELECT COUNT(*) FROM main GROUP BY method HAVING COUNT(*) > 10"),
        
        # LIMIT 测试
        ("LIMIT基础", "SELECT * FROM main LIMIT 10"),
        ("LIMIT + OFFSET", "SELECT * FROM main LIMIT 10 OFFSET 5"),
        ("LIMIT旧语法", "SELECT * FROM main LIMIT 5, 10"),
        
        # WHERE 复杂条件
        ("WHERE LIKE", "SELECT * FROM main WHERE method LIKE '%GET%'"),
        ("WHERE BETWEEN", "SELECT * FROM main WHERE size BETWEEN 100 AND 1000"),
        ("WHERE IN", "SELECT * FROM main WHERE method IN ('GET', 'POST', 'PUT')"),
        ("WHERE IS NULL", "SELECT * FROM main WHERE error_code IS NULL"),
        
        # 聚合函数
        ("COUNT(*)", "SELECT COUNT(*) FROM main"),
        ("SUM/AVG/MIN/MAX", "SELECT SUM(size), AVG(size), MIN(size), MAX(size) FROM main"),
        ("COUNT DISTINCT", "SELECT COUNT(DISTINCT method) FROM main"),
        
        # JOIN 基础
        ("INNER JOIN", "SELECT * FROM orders o INNER JOIN customers c ON o.customer_id = c.id"),
        ("LEFT JOIN", "SELECT * FROM orders o LEFT JOIN customers c ON o.customer_id = c.id"),
        ("RIGHT JOIN", "SELECT * FROM orders o RIGHT JOIN customers c ON o.customer_id = c.id"),
        
        # 复合查询
        ("UNION", "SELECT method FROM main UNION SELECT action FROM logs"),
        ("UNION ALL", "SELECT method FROM main UNION ALL SELECT action FROM logs"),
        
        # 子查询
        ("WHERE子查询", "SELECT * FROM main WHERE customer_id IN (SELECT id FROM customers WHERE active = 1)"),
        ("FROM子查询", "SELECT * FROM (SELECT * FROM main WHERE method = 'GET') t"),
        
        # CASE表达式
        ("CASE WHEN", "SELECT CASE WHEN method = 'GET' THEN 'read' ELSE 'write' END FROM main"),
        ("CASE简单形式", "SELECT CASE method WHEN 'GET' THEN 'read' WHEN 'POST' THEN 'write' END FROM main"),
        
        # 窗口函数
        ("ROW_NUMBER", "SELECT *, ROW_NUMBER() OVER (ORDER BY size DESC) FROM main"),
        ("PARTITION BY", "SELECT *, COUNT(*) OVER (PARTITION BY method) FROM main"),
        
        # 数据类型转换
        ("CAST", "SELECT CAST(size AS INTEGER) FROM main"),
        ("类型转换表达式", "SELECT size::INTEGER FROM main"),
    ]
    
    print("=== 炎凰SQL基础关键词测试 ===\n")
    
    success_count = 0
    total_count = len(test_cases)
    
    for description, sql in test_cases:
        print(f"测试: {description}")
        print(f"SQL: {sql}")
        
        try:
            # 解析测试
            parser = Yanhuang.Parser()
            tokens = Yanhuang.Tokenizer().tokenize(sql)
            ast = parser.parse(tokens, sql)[0]
            
            # 生成测试
            generator = Yanhuang.Generator()
            generated_sql = generator.sql(ast)
            
            print(f"✅ 解析成功")
            print(f"✅ 生成: {generated_sql}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            
        print("-" * 80)
    
    print(f"\n=== 测试总结 ===")
    print(f"成功: {success_count}/{total_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 所有基础关键词都正常工作！")
    else:
        print("⚠️  部分基础关键词需要修复")

if __name__ == "__main__":
    test_basic_keywords() 