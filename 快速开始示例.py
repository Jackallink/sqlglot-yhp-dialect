#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
炎凰数据SQL方言快速开始示例
========================

展示如何使用独立部署的炎凰方言包进行SQL转换
"""

def example_basic_usage():
    """示例1：基础使用方法"""
    print("=" * 60)
    print("示例1：基础使用方法")
    print("=" * 60)
    
    # 导入炎凰方言包
    from sqlglot_yanhuang import transpile_to_yanhuang
    
    # PostgreSQL SQL示例
    postgresql_sqls = [
        "SELECT EXTRACT(year FROM CURRENT_TIMESTAMP)",
        "SELECT 'Hello' || ' ' || 'World'",
        "SELECT CARDINALITY(ARRAY[1,2,3,4,5])",
        "SELECT user_id, COUNT(*) FROM orders WHERE created_at >= NOW() - INTERVAL '7 days' GROUP BY user_id"
    ]
    
    print("PostgreSQL → 炎凰数据转换示例：\n")
    
    for i, sql in enumerate(postgresql_sqls, 1):
        print(f"示例 {i}:")
        print(f"PostgreSQL: {sql}")
        
        # 转换为炎凰方言
        yanhuang_sql = transpile_to_yanhuang(sql)
        print(f"炎凰数据:   {yanhuang_sql}")
        print()

def example_sqlglot_integration():
    """示例2：SQLGlot原生API集成"""
    print("=" * 60)
    print("示例2：SQLGlot原生API集成")
    print("=" * 60)
    
    # 导入炎凰方言包（自动注册）
    import sqlglot_yanhuang
    # 导入SQLGlot
    import sqlglot
    
    # 测试SQL
    test_sql = "SELECT EXTRACT(month FROM CURRENT_TIMESTAMP) as current_month"
    
    print("多方言转换示例：\n")
    
    # PostgreSQL → 炎凰
    yanhuang_result = sqlglot.transpile(test_sql, read="postgres", write="yanhuang")[0]
    print(f"PostgreSQL → 炎凰: {yanhuang_result}")
    
    # 炎凰 → MySQL
    mysql_result = sqlglot.transpile(yanhuang_result, read="yanhuang", write="mysql")[0]
    print(f"炎凰 → MySQL:      {mysql_result}")
    
    # 炎凰 → BigQuery
    bigquery_result = sqlglot.transpile(yanhuang_result, read="yanhuang", write="bigquery")[0]
    print(f"炎凰 → BigQuery:   {bigquery_result}")
    
    print()

def example_advanced_features():
    """示例3：高级功能展示"""
    print("=" * 60)
    print("示例3：高级功能展示")  
    print("=" * 60)
    
    from sqlglot_yanhuang import transpile_to_yanhuang, parse_yanhuang
    
    # LATERAL JOIN转换
    lateral_sql = """
    SELECT u.username, stats.order_count
    FROM users u
    LEFT JOIN LATERAL (
        SELECT COUNT(*) as order_count
        FROM orders o
        WHERE o.user_id = u.id
        AND o.created_at >= CURRENT_DATE - INTERVAL '30 days'
    ) stats ON true
    """
    
    print("LATERAL JOIN → OUTER APPLY 转换:")
    print(f"PostgreSQL:\n{lateral_sql.strip()}")
    
    yanhuang_lateral = transpile_to_yanhuang(lateral_sql)
    print(f"\n炎凰数据:\n{yanhuang_lateral}")
    print()
    
    # 复杂查询转换
    complex_sql = """
    WITH monthly_sales AS (
        SELECT 
            DATE_TRUNC('month', order_date) as month,
            SUM(amount) as total_sales,
            COUNT(*) as order_count
        FROM orders 
        WHERE order_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY DATE_TRUNC('month', order_date)
    )
    SELECT 
        month,
        total_sales,
        order_count,
        LAG(total_sales) OVER (ORDER BY month) as prev_month_sales,
        total_sales - LAG(total_sales) OVER (ORDER BY month) as sales_growth
    FROM monthly_sales
    ORDER BY month
    """
    
    print("复杂查询转换示例:")
    print("PostgreSQL: [复杂CTE + 窗口函数查询]")
    
    yanhuang_complex = transpile_to_yanhuang(complex_sql)
    print(f"炎凰数据: {yanhuang_complex}")
    print()

def example_error_handling():
    """示例4：错误处理"""
    print("=" * 60)
    print("示例4：错误处理和警告")
    print("=" * 60)
    
    from sqlglot_yanhuang import transpile_to_yanhuang
    import warnings
    
    # 捕获警告
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # 包含不支持函数的SQL
        sql_with_unsupported = "SELECT ARRAY_LOWER(ARRAY[1,2,3], 1)"
        
        try:
            result = transpile_to_yanhuang(sql_with_unsupported)
            print(f"SQL: {sql_with_unsupported}")
            print(f"结果: {result}")
            
            # 显示警告
            if w:
                print("警告信息:")
                for warning in w:
                    print(f"  - {warning.message}")
            else:
                print("无警告产生")
                
        except Exception as e:
            print(f"转换失败: {e}")
    
    print()
    
    # 错误处理示例
    try:
        invalid_sql = "SELECT FROM WHERE"
        result = transpile_to_yanhuang(invalid_sql)
        print(f"意外成功: {result}")
    except Exception as e:
        print(f"正确捕获SQL语法错误: {type(e).__name__}: {e}")
    
    print()

def main():
    """主函数"""
    print("🚀 炎凰数据SQL方言快速开始示例")
    print("=" * 80)
    print("这个示例展示了如何使用独立部署的炎凰方言包进行SQL转换")
    print("确保已安装：pip install sqlglot sqlglot_yanhuang_dialect-1.0.0-py3-none-any.whl")
    print("=" * 80)
    
    try:
        # 检查环境
        import sqlglot_yanhuang
        print(f"✅ 炎凰方言包版本: {getattr(sqlglot_yanhuang, '__version__', 'Unknown')}")
        
        import sqlglot
        print(f"✅ SQLGlot版本: {getattr(sqlglot, '__version__', 'Unknown')}")
        print()
        
        # 运行示例
        example_basic_usage()
        example_sqlglot_integration()
        example_advanced_features()
        example_error_handling()
        
        print("=" * 80)
        print("🎉 所有示例运行完成！")
        print("💡 您现在可以在自己的项目中使用炎凰数据SQL方言转换功能了")
        print("=" * 80)
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已正确安装sqlglot和炎凰方言包")
        print("安装命令:")
        print("  pip install sqlglot")
        print("  pip install sqlglot_yanhuang_dialect-1.0.0-py3-none-any.whl")
    
    except Exception as e:
        print(f"❌ 运行错误: {e}")

if __name__ == "__main__":
    main() 