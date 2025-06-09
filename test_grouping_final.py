#!/usr/bin/env python3
"""
炎凰数据GROUPING和GROUPING SETS功能测试
测试所有相关功能是否正常工作
"""

import sqlglot
import warnings

def test_grouping_functionality():
    """测试GROUPING相关功能"""
    print("=== 炎凰数据GROUPING功能测试 ===\n")
    
    test_cases = [
        {
            "name": "GROUPING SETS语法",
            "sql": "SELECT region, SUM(sales) FROM sales GROUP BY GROUPING SETS ((region), ())",
            "should_warn": True,
            "should_contain": ["GROUP BY", "SUM(sales)"],
            "should_not_contain": ["GROUPING SETS"]
        },
        {
            "name": "ROLLUP语法", 
            "sql": "SELECT a, b, SUM(c) FROM t GROUP BY ROLLUP(a, b)",
            "should_warn": True,
            "should_contain": ["GROUP BY", "SUM(c)"],
            "should_not_contain": ["ROLLUP"]
        },
        {
            "name": "CUBE语法",
            "sql": "SELECT x, y, COUNT(*) FROM t GROUP BY CUBE(x, y)", 
            "should_warn": True,
            "should_contain": ["GROUP BY", "COUNT(*)"],
            "should_not_contain": ["CUBE"]
        },
        {
            "name": "GROUPING函数",
            "sql": "SELECT region, GROUPING(region) FROM sales GROUP BY region",
            "should_warn": True,
            "should_contain": ["GROUP BY", "region"],
            "should_not_contain": ["GROUPING(region)"]
        },
        {
            "name": "复杂GROUPING SETS",
            "sql": """
            SELECT region, product, SUM(sales), GROUPING(region, product)
            FROM sales_table 
            GROUP BY GROUPING SETS ((region, product), (region), ())
            """,
            "should_warn": True,
            "should_contain": ["SUM(sales)", "region", "product"],
            "should_not_contain": ["GROUPING SETS", "GROUPING(region, product)"]
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. 测试 {test_case['name']}")
        print(f"   输入: {test_case['sql'].strip()}")
        
        try:
            # 捕获警告
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                
                result = sqlglot.transpile(
                    test_case['sql'], 
                    read="postgres", 
                    write="yanhuang"
                )[0]
                
                print(f"   输出: {result}")
                
                # 检查是否应该有警告
                if test_case['should_warn']:
                    if not w:
                        print(f"   ❌ 期望有警告但没有警告")
                        continue
                    else:
                        print(f"   ✅ 正确生成了警告:")
                        for warning in w:
                            print(f"      - {warning.message}")
                else:
                    if w:
                        print(f"   ❌ 不应该有警告但生成了警告: {[str(warning.message) for warning in w]}")
                        continue
                
                # 检查输出应该包含的内容
                all_contains_pass = True
                for should_contain in test_case['should_contain']:
                    if should_contain not in result:
                        print(f"   ❌ 输出应该包含 '{should_contain}' 但没有找到")
                        all_contains_pass = False
                
                # 检查输出不应该包含的内容
                all_not_contains_pass = True
                for should_not_contain in test_case['should_not_contain']:
                    if should_not_contain in result:
                        print(f"   ❌ 输出不应该包含 '{should_not_contain}' 但找到了")
                        all_not_contains_pass = False
                
                if all_contains_pass and all_not_contains_pass:
                    print(f"   ✅ 测试通过")
                    success_count += 1
                else:
                    print(f"   ❌ 测试失败")
                    
        except Exception as e:
            print(f"   ❌ 测试出错: {e}")
        
        print()  # 空行分隔
    
    print(f"=== 测试总结 ===")
    print(f"通过: {success_count}/{total_count}")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("🎉 所有GROUPING功能测试通过!")
        return True
    else:
        print("❌ 部分测试失败，需要检查实现")
        return False

def test_alternative_solutions():
    """测试建议的替代方案"""
    print("\n=== 测试替代方案 ===\n")
    
    # 测试UNION ALL替代GROUPING SETS
    union_sql = """
    SELECT region, product, SUM(sales) FROM sales_table GROUP BY region, product
    UNION ALL
    SELECT region, NULL, SUM(sales) FROM sales_table GROUP BY region
    UNION ALL  
    SELECT NULL, NULL, SUM(sales) FROM sales_table
    """
    
    print("1. 测试UNION ALL替代方案")
    print(f"   输入: {union_sql.strip()}")
    
    try:
        result = sqlglot.transpile(union_sql, read="postgres", write="yanhuang")[0]
        print(f"   输出: {result}")
        
        if "UNION ALL" in result and "SUM(sales)" in result:
            print("   ✅ UNION ALL替代方案可以正常工作")
        else:
            print("   ❌ UNION ALL替代方案有问题")
    except Exception as e:
        print(f"   ❌ UNION ALL测试出错: {e}")
    
    print()
    
    # 测试CASE WHEN替代GROUPING函数
    case_when_sql = """
    SELECT 
        region,
        SUM(sales),
        CASE WHEN region IS NULL THEN 1 ELSE 0 END as region_grouping
    FROM sales_table 
    GROUP BY region
    """
    
    print("2. 测试CASE WHEN替代方案")
    print(f"   输入: {case_when_sql.strip()}")
    
    try:
        result = sqlglot.transpile(case_when_sql, read="postgres", write="yanhuang")[0]
        print(f"   输出: {result}")
        
        if "CASE WHEN" in result and "SUM(sales)" in result:
            print("   ✅ CASE WHEN替代方案可以正常工作")
        else:
            print("   ❌ CASE WHEN替代方案有问题")
    except Exception as e:
        print(f"   ❌ CASE WHEN测试出错: {e}")

if __name__ == "__main__":
    success = test_grouping_functionality()
    test_alternative_solutions()
    
    if success:
        print("\n🎉 GROUPING功能实现完成且测试通过!")
    else:
        print("\n❌ 需要进一步调试GROUPING功能实现") 