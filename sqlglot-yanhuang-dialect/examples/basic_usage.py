#!/usr/bin/env python3
"""
炎凰数据 SQL 方言包基本使用示例
"""

from sqlglot_yanhuang import transpile_to_yanhuang, parse_yanhuang
import sqlglot

def basic_examples():
    """基本转换示例"""
    print("🚀 炎凰数据 SQL 方言包 - 基本使用示例")
    print("=" * 50)
    
    examples = [
        {
            "name": "函数映射",
            "sql": "SELECT EXTRACT(year FROM created_at), CURRENT_TIMESTAMP"
        },
        {
            "name": "字符串连接",
            "sql": "SELECT first_name || ' ' || last_name AS full_name"
        },
        {
            "name": "LATERAL JOIN",
            "sql": """
                SELECT u.user_id, stats.order_count
                FROM users u
                LEFT JOIN LATERAL (
                    SELECT COUNT(*) AS order_count
                    FROM orders o
                    WHERE o.user_id = u.user_id
                ) stats ON true
            """
        },
        {
            "name": "数组函数",
            "sql": "SELECT ARRAY_TO_STRING(ARRAY[1,2,3], ','), CARDINALITY(ARRAY[1,2,3])"
        },
        {
            "name": "正则表达式",
            "sql": "SELECT name FROM users WHERE email ~ '^[a-z]+@[a-z]+\\.[a-z]+$'"
        },
        {
            "name": "类型转换",
            "sql": "SELECT id::text, created_at::date"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n📋 示例 {i}: {example['name']}")
        print("-" * 40)
        print(f"PostgreSQL:")
        print(example['sql'].strip())
        
        try:
            result = transpile_to_yanhuang(example['sql'])
            print(f"\n炎凰数据:")
            print(result)
        except Exception as e:
            print(f"❌ 转换失败: {e}")

def advanced_examples():
    """高级功能示例"""
    print("\n\n🔧 高级功能示例")
    print("=" * 30)
    
    # 复杂查询示例
    complex_sql = """
        WITH monthly_stats AS (
            SELECT 
                DATE_TRUNC('month', created_at) AS month,
                COUNT(*) AS total_orders,
                SUM(amount) AS total_amount
            FROM orders
            WHERE created_at >= CURRENT_DATE - INTERVAL '1 year'
            GROUP BY DATE_TRUNC('month', created_at)
        )
        SELECT 
            month,
            total_orders,
            total_amount,
            RANK() OVER (ORDER BY total_amount DESC) AS amount_rank
        FROM monthly_stats
        ORDER BY month DESC
    """
    
    print("\n📊 复杂查询转换:")
    print("PostgreSQL:")
    print(complex_sql.strip())
    
    try:
        result = transpile_to_yanhuang(complex_sql)
        print(f"\n炎凰数据:")
        print(result)
    except Exception as e:
        print(f"❌ 转换失败: {e}")
    
    # 使用 SQLGlot 直接转换
    print("\n\n🛠 直接使用 SQLGlot:")
    direct_examples = [
        "SELECT NOW()",
        "SELECT ARRAY_LENGTH(ARRAY[1,2,3])",
        "SELECT REGEXP_LIKE('test', '^test$')"
    ]
    
    for sql in direct_examples:
        try:
            result = sqlglot.transpile(sql, read="postgres", write="yanhuang")[0]
            print(f"{sql} → {result}")
        except Exception as e:
            print(f"{sql} → 错误: {e}")

def performance_showcase():
    """性能展示"""
    print("\n\n⚡ 性能展示")
    print("=" * 20)
    
    import time
    
    # 大量SQL转换测试
    test_sqls = [
        "SELECT EXTRACT(year FROM created_at)",
        "SELECT first_name || ' ' || last_name",
        "SELECT ARRAY_TO_STRING(ARRAY[1,2,3], ',')",
        "SELECT name FROM users WHERE email ~ '^test'",
        "SELECT id::text FROM users"
    ] * 100  # 500条SQL
    
    start_time = time.time()
    
    results = []
    for sql in test_sqls:
        try:
            result = transpile_to_yanhuang(sql)
            results.append(result)
        except:
            pass
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ 转换 {len(test_sqls)} 条 SQL")
    print(f"⏱ 总时间: {duration:.3f} 秒")
    print(f"🚀 平均速度: {len(test_sqls)/duration:.1f} 条/秒")
    print(f"✅ 成功率: {len(results)/len(test_sqls)*100:.1f}%")

if __name__ == "__main__":
    basic_examples()
    advanced_examples()
    performance_showcase() 