#!/usr/bin/env python3
"""
炎凰SQL语法覆盖度测试
检查当前实现与炎凰SQL文档的差异
"""

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang
from sqlglot import exp, parse_one, transpile
import traceback

def test_function_coverage():
    """测试函数覆盖度"""
    print("=== 函数覆盖度测试 ===")
    
    # 根据文档定义的函数类别
    function_categories = {
        "字符串函数": [
            "UPPER", "LOWER", "SUBSTR", "SUBSTRING", "POSITION", "CHAR_LENGTH", 
            "CHARACTER_LENGTH", "LEFT", "RIGHT", "REVERSE", "REPEAT", "LPAD", 
            "RPAD", "TRIM", "LTRIM", "RTRIM", "REPLACE", "TRANSLATE", "ASCII", 
            "CHR", "INITCAP", "SPLIT_PART", "CONCAT", "LENGTH", "COALESCE"
        ],
        "数学函数": [
            "ABS", "CEIL", "CEILING", "FLOOR", "ROUND", "SQRT", "POWER", "POW",
            "MOD", "SIN", "COS", "TAN", "ASIN", "ACOS", "ATAN", "ATAN2",
            "LOG", "LOG10", "LN", "EXP", "SIGN", "TRUNC", "TRUNCATE",
            "RANDOM", "PI", "DEGREES", "RADIANS", "GREATEST", "LEAST"
        ],
        "日期时间函数": [
            "NOW", "CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME",
            "EXTRACT", "DATE_PART", "DATE_TRUNC", "AGE", "TO_TIMESTAMP",
            "TO_DATE", "TO_CHAR", "EPOCH", "DATEADD", "DATEDIFF"
        ],
        "条件函数": [
            "IF", "DECODE", "CASE", "COALESCE", "NULLIF", "GREATEST", "LEAST"
        ],
        "类型转换函数": [
            "CAST", "TO_NUMBER", "TO_BINARY"
        ],
        "聚合函数": [
            "COUNT", "SUM", "AVG", "MAX", "MIN", "MAX_STR", "MIN_STR",
            "STRING_AGG", "STDDEV_POP", "STDDEV_SAMP", "VAR_POP", "VAR_SAMP",
            "QUANTILE_T_DIGEST", "PERCENTILE", "APPROX_COUNT_DISTINCT",
            "APPROX_MEDIAN", "PRODUCT", "LATEST_VALUE", "EARLIEST_VALUE",
            "FIRST_VALUE", "LAST_VALUE", "ARRAY_AGG", "JSON_AGG", "JSON_OBJECT_AGG"
        ],
        "窗口函数": [
            "ROW_NUMBER", "RANK", "DENSE_RANK", "PERCENT_RANK", "CUME_DIST",
            "NTILE", "LAG", "LEAD", "FIRST_VALUE", "LAST_VALUE"
        ],
        "炎凰SQL特有函数": [
            "CONTAINS", "TIME_BUCKET", "REGEX_EXTRACT", "REGEX_MATCH", "REGEX_REPLACE",
            "IP_TO_COUNTRY", "IP_TO_REGION", "IP_TO_CITY", "GEOHASH", "GEOHASH_DECODE",
            "UUID", "MD5", "SHA1", "SHA256", "BASE64_ENCODE", "BASE64_DECODE",
            "URL_ENCODE", "URL_DECODE"
        ],
        "表函数": [
            "GENERATE_SERIES", "PARSE_JSON", "PARSE_CSV", "PARSE_REGEX", "PARSE_KV",
            "PARSE_XML", "PARSE_URL", "PARSE_USER_AGENT", "IP_LOCATION", "GEO_DISTANCE",
            "LOAD_CSV", "LOAD_JSON", "LOAD_PARQUET", "LOAD_XML", "EXPLODE",
            "EXPLODE_OUTER", "POSEXPLODE", "POSEXPLODE_OUTER", "UNNEST"
        ]
    }
    
    implemented_functions = set(Yanhuang.Parser.FUNCTIONS.keys())
    
    for category, functions in function_categories.items():
        print(f"\n{category}:")
        missing = []
        implemented = []
        
        for func in functions:
            if func in implemented_functions:
                implemented.append(func)
            else:
                missing.append(func)
        
        print(f"  已实现 ({len(implemented)}/{len(functions)}): {', '.join(implemented)}")
        if missing:
            print(f"  缺失 ({len(missing)}): {', '.join(missing)}")
    
    print(f"\n总体统计:")
    total_documented = sum(len(funcs) for funcs in function_categories.values())
    total_implemented_documented = sum(
        len([f for f in funcs if f in implemented_functions]) 
        for funcs in function_categories.values()
    )
    print(f"文档化函数总数: {total_documented}")
    print(f"已实现文档化函数: {total_implemented_documented}")
    print(f"文档覆盖率: {total_implemented_documented/total_documented*100:.1f}%")
    print(f"实现函数总数: {len(implemented_functions)}")

def test_syntax_features():
    """测试语法特性覆盖度"""
    print("\n=== 语法特性测试 ===")
    
    # 定义测试用例
    test_cases = [
        ("CTE支持", "WITH t AS (SELECT 1 as a) SELECT * FROM t"),
        ("UNION支持", "SELECT 1 UNION SELECT 2"),
        ("窗口函数基础", "SELECT ROW_NUMBER() OVER(ORDER BY id) FROM main"),
        ("CASE表达式", "SELECT CASE WHEN id > 0 THEN 'positive' ELSE 'other' END FROM main"),
        ("DELETE with ORDER BY LIMIT", "DELETE FROM main WHERE id > 100 ORDER BY id LIMIT 10"),
        ("COLUMNS批量投影", "SELECT COLUMNS('^f[0-9]+$') FROM main"),
        ("COLUMNS EXCEPT", "SELECT COLUMNS('.*') EXCEPT (id) FROM main"),
        ("COLUMNS REPLACE", "SELECT COLUMNS('.*') REPLACE (upper(name) AS name) FROM main"),
        ("SAMPLE语法", "SELECT * FROM main SAMPLE ROW (50.0)"),
        ("VALUES语句", "VALUES (1, 'a'), (2, 'b')"),
        ("DESCRIBE语句", "DESCRIBE main"),
        ("SHOW TABLES", "SHOW TABLES"),
        ("CREATE TABLE ENGINE", "CREATE TABLE test ENGINE=event_set"),
        ("APPLY语法", "SELECT * FROM table1 OUTER APPLY (SELECT * FROM func(table1.id)) AS t"),
        ("PIVOT语法", "PIVOT main ON status USING COUNT(*) GROUP BY category"),
        ("Unicode字符串", "SELECT U&'\\0061bcd' AS unicode_str"),
        ("E字符串转义", "SELECT E'line1\\nline2' AS escaped_str"),
        ("多表合并", "SELECT * FROM table1 | table2"),
        ("CONTAINS函数", "SELECT * FROM main WHERE CONTAINS('keyword')"),
        ("TIME分组", "SELECT COUNT(*) FROM main GROUP BY TIME(interval='1h')")
    ]
    
    supported = []
    unsupported = []
    errors = []
    
    for name, sql in test_cases:
        try:
            result = parse_one(sql, dialect=Yanhuang)
            if result:
                supported.append(name)
                print(f"✅ {name}: 支持")
            else:
                unsupported.append(name)
                print(f"❌ {name}: 解析失败")
        except Exception as e:
            errors.append((name, str(e)))
            print(f"🔥 {name}: 错误 - {e}")
    
    print(f"\n语法特性统计:")
    print(f"支持的特性: {len(supported)}/{len(test_cases)} ({len(supported)/len(test_cases)*100:.1f}%)")
    print(f"不支持的特性: {len(unsupported)}")
    print(f"解析错误: {len(errors)}")
    
    if errors:
        print(f"\n解析错误详情:")
        for name, error in errors:
            print(f"  {name}: {error}")

def test_advanced_syntax():
    """测试高级语法特性"""
    print("\n=== 高级语法特性测试 ===")
    
    advanced_cases = [
        ("嵌套CTE", """
            WITH 
                t1 AS (SELECT id, name FROM users),
                t2 AS (SELECT id, COUNT(*) as cnt FROM orders GROUP BY id)
            SELECT t1.name, t2.cnt FROM t1 JOIN t2 ON t1.id = t2.id
        """),
        ("窗口函数PARTITION BY", """
            SELECT 
                name,
                ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rank
            FROM employees
        """),
        ("复杂CASE表达式", """
            SELECT 
                CASE status 
                    WHEN 1 THEN 'active'
                    WHEN 2 THEN 'inactive' 
                    ELSE 'unknown'
                END as status_name
            FROM main
        """),
        ("子查询IN", """
            SELECT * FROM orders 
            WHERE customer_id IN (SELECT id FROM customers WHERE country = 'China')
        """),
        ("EXISTS子查询", """
            SELECT * FROM orders o
            WHERE EXISTS (SELECT 1 FROM customers c WHERE c.id = o.customer_id)
        """),
        ("COLUMNS正则捕获", """
            SELECT COLUMNS('user_(.*)') AS "host_{0}" FROM main
        """),
        ("星号EXCEPT REPLACE", """
            SELECT * EXCEPT(password) REPLACE (upper(name) as name) FROM users
        """),
        ("复杂PIVOT", """
            PIVOT orders 
            ON status IN ('pending', 'completed', 'cancelled')
            USING SUM(amount), COUNT(*)
            GROUP BY customer_id
        """),
        ("表函数APPLY", """
            SELECT u.*, p.product_name
            FROM users u
            OUTER APPLY (
                SELECT TOP 1 product_name 
                FROM purchases 
                WHERE user_id = u.id 
                ORDER BY purchase_date DESC
            ) p
        """),
        ("自定义函数调用", """
            SELECT my_custom_function(field1, field2) FROM main
        """)
    ]
    
    for name, sql in advanced_cases:
        try:
            result = parse_one(sql.strip(), dialect=Yanhuang)
            if result:
                print(f"✅ {name}: 支持")
            else:
                print(f"❌ {name}: 解析失败")
        except Exception as e:
            print(f"🔥 {name}: 错误 - {str(e)[:100]}...")

def test_unsupported_features():
    """测试应该被拒绝的不支持特性"""
    print("\n=== 不支持特性测试 ===")
    
    unsupported_cases = [
        ("INTERSECT集合操作", "SELECT 1 INTERSECT SELECT 1"),
        ("EXCEPT集合操作", "SELECT 1 EXCEPT SELECT 1"),  
        ("WITH RECURSIVE", "WITH RECURSIVE t(n) AS (SELECT 1 UNION SELECT n+1 FROM t WHERE n < 10) SELECT * FROM t"),
        ("RANGE窗口框架", "SELECT SUM(amount) OVER (ORDER BY date RANGE BETWEEN INTERVAL '1' DAY PRECEDING AND CURRENT ROW) FROM main"),
        ("GROUPS窗口框架", "SELECT SUM(amount) OVER (ORDER BY id GROUPS BETWEEN 1 PRECEDING AND 1 FOLLOWING) FROM main"),
        ("DELETE RETURNING", "DELETE FROM main WHERE id = 1 RETURNING *"),
        ("TABLESAMPLE语法", "SELECT * FROM main TABLESAMPLE BERNOULLI(50)"),
        ("PRIMARY KEY约束", "CREATE TABLE test (id INT PRIMARY KEY, name VARCHAR(100))"),
        ("FOREIGN KEY约束", "CREATE TABLE test (id INT REFERENCES other_table(id))"),
        ("复杂类型ARRAY", "SELECT ARRAY[1,2,3] as arr"),
        ("复杂类型JSONB", "SELECT '{\"key\": \"value\"}'::JSONB as data"),
        ("复杂类型JSON", "SELECT '{\"key\": \"value\"}'::JSON as data"),
        ("UNIQUE约束", "CREATE TABLE test (id INT UNIQUE, name VARCHAR(100))"),
        ("CHECK约束", "CREATE TABLE test (id INT CHECK (id > 0), name VARCHAR(100))"),
    ]
    
    correctly_rejected = []
    incorrectly_accepted = []
    
    for name, sql in unsupported_cases:
        try:
            result = parse_one(sql, dialect=Yanhuang)
            if result:
                incorrectly_accepted.append(name)
                print(f"⚠️  {name}: 应该被拒绝但被接受了")
            else:
                correctly_rejected.append(name)
                print(f"✅ {name}: 正确拒绝")
        except Exception as e:
            correctly_rejected.append(name)
            print(f"✅ {name}: 正确拒绝 ({str(e)[:50]}...)")
    
    print(f"\n不支持特性统计:")
    print(f"正确拒绝: {len(correctly_rejected)}/{len(unsupported_cases)}")
    print(f"错误接受: {len(incorrectly_accepted)}")

def test_code_generation():
    """测试代码生成质量"""
    print("\n=== 代码生成测试 ===")
    
    generation_cases = [
        ("基础SELECT", "SELECT id, name FROM users"),
        ("函数调用", "SELECT UPPER(name), LENGTH(description) FROM products"),
        ("窗口函数", "SELECT ROW_NUMBER() OVER (ORDER BY id) FROM main"),
        ("CASE表达式", "SELECT CASE WHEN status = 1 THEN 'active' ELSE 'inactive' END FROM main"),
        ("CTE", "WITH t AS (SELECT id FROM users) SELECT * FROM t"),
        ("DECODE函数", "SELECT DECODE(status, 1, 'active', 2, 'inactive', 'unknown') FROM main"),
        ("SAMPLE语法", "SELECT * FROM main SAMPLE ROW (50.0)"),
        ("COLUMNS语法", "SELECT COLUMNS('^field_.*') EXCEPT (field_secret) FROM main"),
        ("CREATE TABLE ENGINE", "CREATE TABLE test ENGINE=event_set WITH (setting1='value1')"),
        ("DELETE with LIMIT", "DELETE FROM main WHERE status = 'old' ORDER BY created_at LIMIT 100")
    ]
    
    for name, sql in generation_cases:
        try:
            # 解析然后重新生成
            parsed = parse_one(sql, dialect=Yanhuang)
            if parsed:
                generated = parsed.sql(dialect=Yanhuang)
                print(f"✅ {name}:")
                print(f"   原始: {sql}")
                print(f"   生成: {generated}")
            else:
                print(f"❌ {name}: 解析失败")
        except Exception as e:
            print(f"🔥 {name}: 错误 - {e}")

def main():
    """主测试函数"""
    print("炎凰SQL语法覆盖度全面测试")
    print("=" * 50)
    
    test_function_coverage()
    test_syntax_features()
    test_advanced_syntax()
    test_unsupported_features()
    test_code_generation()
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    main() 