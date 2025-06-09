#!/usr/bin/env python3
"""
测试炎凰数据不支持GROUPING和GROUPING SETS语法的问题
"""

import sqlglot

def test_grouping_sets_issue():
    """测试GROUPING SETS不支持的问题"""
    
    # 测试GROUPING SETS语法
    sql_with_grouping_sets = """
    SELECT 
        region,
        product_category,
        sales_channel,
        SUM(sales_amount) as total_sales,
        COUNT(*) as record_count
    FROM sales_data
    GROUP BY GROUPING SETS (
        (region, product_category, sales_channel),
        (region, product_category),
        (region),
        ()
    )
    """
    
    print("测试GROUPING SETS语法:")
    print(f"原始SQL:\n{sql_with_grouping_sets}")
    
    try:
        # 解析PostgreSQL SQL
        parsed = sqlglot.parse_one(sql_with_grouping_sets, dialect="postgres")
        print("✅ PostgreSQL解析成功")
        
        # 转换为炎凰方言
        result = parsed.sql(dialect="yanhuang")
        print(f"炎凰转换结果:\n{result}")
        
        # 检查是否包含GROUPING SETS
        if "GROUPING SETS" in result:
            print("❌ 错误：炎凰SQL输出仍包含GROUPING SETS语法")
        else:
            print("⚠️  警告：GROUPING SETS语法被移除，但没有替代方案")
            
    except Exception as e:
        print(f"❌ 错误：{type(e).__name__}: {e}")

def test_grouping_function_issue():
    """测试GROUPING函数不支持的问题"""
    
    # 测试GROUPING函数语法
    sql_with_grouping = """
    SELECT 
        CASE WHEN GROUPING(region) = 1 THEN 'ALL_REGIONS' ELSE region END as region_group,
        CASE WHEN GROUPING(product_category) = 1 THEN 'ALL_CATEGORIES' ELSE product_category END as category_group,
        SUM(sales_amount) as total_sales
    FROM sales_data
    GROUP BY ROLLUP(region, product_category)
    """
    
    print("\n测试GROUPING函数语法:")
    print(f"原始SQL:\n{sql_with_grouping}")
    
    try:
        # 解析PostgreSQL SQL
        parsed = sqlglot.parse_one(sql_with_grouping, dialect="postgres")
        print("✅ PostgreSQL解析成功")
        
        # 转换为炎凰方言
        result = parsed.sql(dialect="yanhuang")
        print(f"炎凰转换结果:\n{result}")
        
        # 检查是否包含GROUPING函数
        if "GROUPING(" in result:
            print("❌ 错误：炎凰SQL输出仍包含GROUPING函数")
        else:
            print("⚠️  警告：GROUPING函数被移除，但没有替代方案")
            
    except Exception as e:
        print(f"❌ 错误：{type(e).__name__}: {e}")

def test_rollup_cube_issue():
    """测试ROLLUP和CUBE不支持的问题"""
    
    # 测试ROLLUP语法
    sql_with_rollup = """
    SELECT 
        region,
        product_category,
        SUM(sales_amount) as total_sales
    FROM sales_data
    GROUP BY ROLLUP(region, product_category)
    """
    
    print("\n测试ROLLUP语法:")
    print(f"原始SQL:\n{sql_with_rollup}")
    
    try:
        parsed = sqlglot.parse_one(sql_with_rollup, dialect="postgres")
        print("✅ PostgreSQL解析成功")
        
        result = parsed.sql(dialect="yanhuang")
        print(f"炎凰转换结果:\n{result}")
        
        if "ROLLUP" in result:
            print("❌ 错误：炎凰SQL输出仍包含ROLLUP语法")
        else:
            print("⚠️  警告：ROLLUP语法被移除，但没有替代方案")
            
    except Exception as e:
        print(f"❌ 错误：{type(e).__name__}: {e}")
    
    # 测试CUBE语法
    sql_with_cube = """
    SELECT 
        region,
        product_category,
        sales_channel,
        SUM(sales_amount) as total_sales
    FROM sales_data
    GROUP BY CUBE(region, product_category, sales_channel)
    """
    
    print("\n测试CUBE语法:")
    print(f"原始SQL:\n{sql_with_cube}")
    
    try:
        parsed = sqlglot.parse_one(sql_with_cube, dialect="postgres")
        print("✅ PostgreSQL解析成功")
        
        result = parsed.sql(dialect="yanhuang")
        print(f"炎凰转换结果:\n{result}")
        
        if "CUBE" in result:
            print("❌ 错误：炎凰SQL输出仍包含CUBE语法")
        else:
            print("⚠️  警告：CUBE语法被移除，但没有替代方案")
            
    except Exception as e:
        print(f"❌ 错误：{type(e).__name__}: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("炎凰数据GROUPING和GROUPING SETS语法支持测试")
    print("=" * 80)
    
    test_grouping_sets_issue()
    test_grouping_function_issue()
    test_rollup_cube_issue()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80) 