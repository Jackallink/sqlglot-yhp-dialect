#!/usr/bin/env python3
"""
测试GROUPING相关语法的警告处理
验证GROUPING函数、GROUPING SETS、ROLLUP、CUBE的警告机制
"""

import warnings
import sqlglot

def test_grouping_warnings():
    """测试GROUPING相关语法的警告处理"""
    
    print("=" * 80)
    print("炎凰数据GROUPING语法警告测试")
    print("=" * 80)
    
    test_cases = [
        {
            "name": "GROUPING函数警告",
            "sql": "SELECT GROUPING(column1) FROM table1",
            "expect_warning": True,
            "warning_keywords": ["GROUPING函数", "不支持", "替代"]
        },
        {
            "name": "GROUPING SETS语法警告", 
            "sql": "SELECT a, b FROM table1 GROUP BY GROUPING SETS ((a, b), (a), ())",
            "expect_warning": True,
            "warning_keywords": ["GROUPING SETS", "不支持", "UNION ALL"]
        },
        {
            "name": "ROLLUP语法警告",
            "sql": "SELECT a, b FROM table1 GROUP BY ROLLUP(a, b)",
            "expect_warning": True,
            "warning_keywords": ["ROLLUP", "不支持", "UNION ALL"]
        },
        {
            "name": "CUBE语法警告",
            "sql": "SELECT a, b FROM table1 GROUP BY CUBE(a, b)",
            "expect_warning": True,
            "warning_keywords": ["CUBE", "不支持", "UNION ALL"]
        },
        {
            "name": "复合GROUPING语法警告",
            "sql": """
            SELECT 
                CASE WHEN GROUPING(region) = 1 THEN 'ALL' ELSE region END,
                SUM(sales)
            FROM sales_data 
            GROUP BY ROLLUP(region, product)
            """,
            "expect_warning": True,
            "warning_keywords": ["GROUPING", "ROLLUP", "不支持"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_case['name']}")
        print(f"SQL: {test_case['sql'].strip()}")
        
        # 捕获警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            try:
                # 1. 解析PostgreSQL SQL
                parsed_ast = sqlglot.parse(test_case['sql'], dialect="postgres")[0]
                print(f"✅ PostgreSQL解析成功")
                
                # 2. 转换为炎凰数据SQL（这里应该产生警告）
                yanhuang_generator = sqlglot.dialects.Yanhuang.Generator()
                result = yanhuang_generator.sql(parsed_ast)
                
                print(f"✅ 炎凰转换成功")
                print(f"转换结果: {result}")
                
                # 检查警告
                if test_case['expect_warning']:
                    if w:
                        print(f"📢 捕获到 {len(w)} 个警告:")
                        for warning in w:
                            warning_msg = str(warning.message)
                            print(f"   • {warning_msg}")
                            
                            # 检查关键词
                            found_keywords = [kw for kw in test_case['warning_keywords'] 
                                            if kw in warning_msg]
                            if found_keywords:
                                print(f"   ✓ 包含预期关键词: {found_keywords}")
                            else:
                                print(f"   ⚠️  未包含预期关键词: {test_case['warning_keywords']}")
                    else:
                        print("❌ 未捕获到预期的警告")
                else:
                    if w:
                        print(f"⚠️  意外捕获到警告: {[str(warning.message) for warning in w]}")
                    else:
                        print("✅ 正确：未产生警告")
                        
            except Exception as e:
                print(f"❌ 转换失败: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("警告测试完成")
    print("=" * 80)

if __name__ == "__main__":
    test_grouping_warnings() 