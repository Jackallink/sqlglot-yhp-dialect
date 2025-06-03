#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

def test_window_functions():
    """测试炎凰SQL窗口函数的实现状态"""
    
    test_cases = [
        # 基本窗口函数（应该支持）
        ("基本窗口函数", "SELECT COUNT(*) OVER (PARTITION BY id ORDER BY time DESC) FROM main", True),
        ("简单PARTITION BY", "SELECT COUNT(*) OVER (PARTITION BY method) FROM main", True),
        ("简单ORDER BY", "SELECT ROW_NUMBER() OVER (ORDER BY size DESC) FROM main", True),
        
        # 聚合窗口函数（应该支持）
        ("SUM窗口函数", "SELECT SUM(size) OVER (PARTITION BY method) FROM main", True),
        ("AVG窗口函数", "SELECT AVG(size) OVER (PARTITION BY method ORDER BY time) FROM main", True),
        ("MIN/MAX窗口函数", "SELECT MIN(size) OVER (PARTITION BY method), MAX(size) OVER (PARTITION BY method) FROM main", True),
        
        # 非聚合窗口函数（应该支持）
        ("ROW_NUMBER", "SELECT ROW_NUMBER() OVER (PARTITION BY group_id ORDER BY price DESC) FROM products", True),
        ("FIRST_VALUE", "SELECT FIRST_VALUE(price) OVER (PARTITION BY group_id ORDER BY price DESC) FROM products", True),
        ("LAST_VALUE", "SELECT LAST_VALUE(price) OVER (PARTITION BY group_id ORDER BY price DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) FROM products", True),
        ("LAG基础", "SELECT LAG(sale_value) OVER (ORDER BY sale_value) FROM sale", True),
        ("LAG带偏移", "SELECT LAG(sale_value, 2) OVER (ORDER BY sale_value) FROM sale", True),
        ("LAG带默认值", "SELECT LAG(sale_value, 1, 0) OVER (ORDER BY sale_value) FROM sale", True),
        ("LEAD基础", "SELECT LEAD(sale_value) OVER (ORDER BY sale_value) FROM sale", True),
        ("LEAD带偏移", "SELECT LEAD(sale_value, 2) OVER (ORDER BY sale_value) FROM sale", True),
        ("LEAD带默认值", "SELECT LEAD(sale_value, 1, 0) OVER (ORDER BY sale_value) FROM sale", True),
        
        # 窗口框架子句（ROWS支持）
        ("ROWS CURRENT ROW", "SELECT SUM(size) OVER (ORDER BY time ROWS CURRENT ROW) FROM main", True),
        ("ROWS UNBOUNDED PRECEDING", "SELECT SUM(size) OVER (ORDER BY time ROWS UNBOUNDED PRECEDING) FROM main", True),
        ("ROWS UNBOUNDED FOLLOWING", "SELECT SUM(size) OVER (ORDER BY time ROWS UNBOUNDED FOLLOWING) FROM main", True),
        ("ROWS BETWEEN", "SELECT SUM(size) OVER (ORDER BY time ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main", True),
        ("ROWS BETWEEN完整", "SELECT SUM(size) OVER (ORDER BY time ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) FROM main", True),
        ("ROWS数字偏移", "SELECT SUM(size) OVER (ORDER BY time ROWS BETWEEN 2 PRECEDING AND 1 FOLLOWING) FROM main", True),
        
        # 文档示例测试（应该支持）
        ("文档示例1", "SELECT SUM(size) OVER(PARTITION BY agent) FROM main WHERE _datatype='nginx.access_log'", True),
        ("文档示例2", "SELECT SUM(size) OVER(PARTITION BY agent ORDER BY method ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main WHERE _datatype='nginx.access_log'", True),
        
        # 不支持的功能（应该报错或有限制）
        ("ORDER BY中使用窗口函数", "SELECT * FROM main ORDER BY COUNT(*) OVER (PARTITION BY id)", False),
        ("窗口函数运算", "SELECT (COUNT(*) OVER ()) + 1 FROM main", False),
        ("WINDOW子句", "SELECT COUNT(*) OVER w FROM main WINDOW w AS (PARTITION BY id)", False),
        ("RANGE框架", "SELECT SUM(size) OVER (ORDER BY time RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main", False),
        ("GROUPS框架", "SELECT SUM(size) OVER (ORDER BY time GROUPS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main", False),
        
        # 复杂场景
        ("多个窗口函数", "SELECT ROW_NUMBER() OVER (ORDER BY size), RANK() OVER (ORDER BY size) FROM main", True),
        ("嵌套子查询中的窗口函数", "SELECT * FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY size) as rn FROM main) WHERE rn <= 10", True),
    ]
    
    print("=== 炎凰SQL窗口函数测试 ===\n")
    
    success_count = 0
    total_count = len(test_cases)
    expected_pass = 0
    expected_fail = 0
    
    for description, sql, should_pass in test_cases:
        if should_pass:
            expected_pass += 1
        else:
            expected_fail += 1
            
        print(f"测试: {description}")
        print(f"SQL: {sql}")
        print(f"预期: {'应该成功' if should_pass else '应该失败/有限制'}")
        
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
            
            if should_pass:
                print("✅ 符合预期")
                success_count += 1
            else:
                print("❌ 预期失败但实际成功")
                
        except Exception as e:
            print(f"❌ 失败: {e}")
            
            if not should_pass:
                print("✅ 符合预期（应该失败）")
                success_count += 1
            else:
                print("❌ 预期成功但实际失败")
                
        print("-" * 100)
    
    print(f"\n=== 测试总结 ===")
    print(f"总测试数: {total_count}")
    print(f"预期成功: {expected_pass}")
    print(f"预期失败: {expected_fail}")
    print(f"实际符合预期: {success_count}/{total_count}")
    print(f"符合率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 窗口函数完全符合炎凰SQL规范！")
    else:
        print("⚠️  窗口函数实现需要调整以符合炎凰SQL规范")

if __name__ == "__main__":
    test_window_functions() 