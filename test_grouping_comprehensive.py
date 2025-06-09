#!/usr/bin/env python3
"""
炎凰数据GROUPING功能综合测试
测试所有GROUPING相关功能的完整性和正确性
"""

import sqlglot
import warnings

def test_grouping_comprehensive():
    """综合测试GROUPING相关功能"""
    print("=== 炎凰数据GROUPING功能综合测试 ===\n")
    
    test_cases = [
        {
            "name": "纯GROUPING SETS语法",
            "sql": "SELECT region, SUM(sales) FROM sales GROUP BY GROUPING SETS ((region), ())",
            "should_warn": True,
            "should_contain": ["SELECT", "SUM(sales)"],
            "should_not_contain": ["GROUPING SETS"],
            "note": "纯GROUPING SETS应该被移除，整个GROUP BY被移除"
        },
        {
            "name": "GROUPING SETS + 普通列",
            "sql": "SELECT region, dept, SUM(sales) FROM sales GROUP BY dept, GROUPING SETS ((region), ())",
            "should_warn": True,
            "should_contain": ["GROUP BY dept", "SUM(sales)"],
            "should_not_contain": ["GROUPING SETS"],
            "note": "GROUPING SETS被移除，但保留普通GROUP BY列"
        },
        {
            "name": "纯ROLLUP语法",
            "sql": "SELECT a, b, SUM(c) FROM t GROUP BY ROLLUP(a, b)",
            "should_warn": True,
            "should_contain": ["SELECT", "SUM(c)"],
            "should_not_contain": ["ROLLUP"],
            "note": "纯ROLLUP应该被移除，整个GROUP BY被移除"
        },
        {
            "name": "ROLLUP + 普通列",
            "sql": "SELECT a, b, c, SUM(d) FROM t GROUP BY c, ROLLUP(a, b)",
            "should_warn": True,
            "should_contain": ["GROUP BY c", "SUM(d)"],
            "should_not_contain": ["ROLLUP"],
            "note": "ROLLUP被移除，但保留普通GROUP BY列"
        },
        {
            "name": "纯CUBE语法",
            "sql": "SELECT x, y, COUNT(*) FROM t GROUP BY CUBE(x, y)",
            "should_warn": True,
            "should_contain": ["SELECT", "COUNT(*)"],
            "should_not_contain": ["CUBE"],
            "note": "纯CUBE应该被移除，整个GROUP BY被移除"
        },
        {
            "name": "CUBE + 普通列",
            "sql": "SELECT x, y, z, COUNT(*) FROM t GROUP BY z, CUBE(x, y)",
            "should_warn": True,
            "should_contain": ["GROUP BY z", "COUNT(*)"],
            "should_not_contain": ["CUBE"],
            "note": "CUBE被移除，但保留普通GROUP BY列"
        },
        {
            "name": "GROUPING函数",
            "sql": "SELECT region, GROUPING(region), SUM(sales) FROM sales GROUP BY region",
            "should_warn": True,
            "should_contain": ["GROUP BY region", "SUM(sales)", "0 /*"],
            "should_not_contain": ["GROUPING(region)"],
            "note": "GROUPING函数被替换为固定值0并添加注释"
        },
        {
            "name": "混合GROUPING语法",
            "sql": """SELECT region, product, GROUPING(region), SUM(sales)
                     FROM sales_table 
                     GROUP BY product, GROUPING SETS ((region), ())""",
            "should_warn": True,
            "should_contain": ["GROUP BY product", "SUM(sales)", "0 /*"],
            "should_not_contain": ["GROUPING SETS", "GROUPING(region)"],
            "note": "GROUPING函数和GROUPING SETS都被处理，保留普通列"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. 测试 {case['name']}")
        print(f"   输入: {case['sql']}")
        
        # 捕获警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            try:
                result = sqlglot.transpile(case['sql'], read="postgres", write="yanhuang")[0]
                print(f"   输出: {result}")
                
                # 检查警告
                if case['should_warn']:
                    if w:
                        print(f"   ✅ 正确生成了警告:")
                        for warning in w:
                            print(f"      - {warning.message}")
                    else:
                        print(f"   ❌ 期望有警告但没有警告")
                        continue
                else:
                    if w:
                        print(f"   ❌ 不期望警告但生成了警告:")
                        for warning in w:
                            print(f"      - {warning.message}")
                        continue
                    else:
                        print(f"   ✅ 正确：没有生成警告")
                
                # 检查输出应该包含的内容
                for content in case['should_contain']:
                    if content in result:
                        print(f"   ✅ 输出包含预期内容: '{content}'")
                    else:
                        print(f"   ❌ 输出缺少预期内容: '{content}'")
                        continue
                
                # 检查输出不应该包含的内容
                for content in case['should_not_contain']:
                    if content not in result:
                        print(f"   ✅ 输出正确移除了: '{content}'")
                    else:
                        print(f"   ❌ 输出仍包含不应该有的内容: '{content}'")
                        continue
                
                print(f"   ✅ 测试通过 - {case['note']}")
                passed += 1
                
            except Exception as e:
                print(f"   ❌ 测试异常: {e}")
        
        print()
    
    print("=== 测试总结 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("✅ 所有GROUPING功能测试通过！")
    else:
        print("❌ 部分测试失败，需要进一步检查")
    
    return passed == total

if __name__ == "__main__":
    test_grouping_comprehensive() 