#!/usr/bin/env python3
"""
炎凰SQL方言完整性检查脚本
验证所有语法文档中提到的功能项是否都已实现
"""

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

def test_completeness():
    """验证炎凰SQL方言的完整性"""
    
    print("=" * 60)
    print("炎凰SQL方言完整性检查")
    print("=" * 60)
    
    # === 1. SQL标识符测试 ===
    print("\n1. SQL标识符支持:")
    identifier_tests = [
        # 不带引号的标识符
        "SELECT field, Field FROM main",  # 大小写敏感
        "SELECT _source AS 来源 FROM main",  # 中文别名
        
        # 单引号标识符（字符串常量）
        "SELECT 'literal value' AS field_name FROM main LIMIT 1",
        "SELECT E'abc\\ndef\\gh' AS field_name FROM main LIMIT 1",  # C-style转义
        "SELECT U&'\\0061bcd' AS field_name FROM main LIMIT 1",     # Unicode编码
        "SELECT U&'!0061bcd!!' UESCAPE '!' AS field_name FROM main LIMIT 1",  # 自定义转义
        
        # 双引号标识符
        'SELECT "field left", "FIELD right" FROM main',
        'SELECT 1 AS "escape double ""quotes"',
    ]
    
    for test in identifier_tests:
        try:
            ast = sqlglot.parse_one(test, dialect="yanhuang")
            print(f"✅ {test}")
        except Exception as e:
            print(f"❌ {test} - 错误: {e}")
    
    # === 2. 数值类型运算测试 ===
    print("\n2. 数值类型运算:")
    arithmetic_tests = [
        "SELECT a + b, a - b, a * b, a / b, a % b FROM main",
        "SELECT (a + b) * c / (d - e) FROM main",
        "SELECT 1 + 2 * 3 - 4 / 5 % 6 FROM main",
    ]
    
    for test in arithmetic_tests:
        try:
            ast = sqlglot.parse_one(test, dialect="yanhuang")
            print(f"✅ {test}")
        except Exception as e:
            print(f"❌ {test} - 错误: {e}")
    
    # === 3. 标量函数测试 ===
    print("\n3. 标量函数支持:")
    scalar_function_tests = [
        # 字符串函数
        "SELECT UPPER(name), LOWER(name), LENGTH(name) FROM main",
        "SELECT SUBSTRING(name, 1, 5), SUBSTR(name, 1, 5) FROM main",
        "SELECT LEFT(name, 3), RIGHT(name, 3), REVERSE(name) FROM main",
        "SELECT TRIM(name), LTRIM(name), RTRIM(name) FROM main",
        "SELECT REPLACE(name, 'old', 'new'), REPEAT(name, 3) FROM main",
        "SELECT LPAD(name, 10, '0'), RPAD(name, 10, '0') FROM main",
        "SELECT POSITION('e' IN name), CHAR_LENGTH(name) FROM main",
        "SELECT ASCII(name), CHR(65), INITCAP(name) FROM main",
        
        # 数学函数
        "SELECT ABS(value), SIGN(value), SQRT(value) FROM main",
        "SELECT ROUND(value, 2), FLOOR(value), CEIL(value) FROM main",
        "SELECT POWER(value, 2), POW(value, 2), MOD(value, 10) FROM main",
        "SELECT SIN(angle), COS(angle), TAN(angle) FROM main",
        "SELECT ASIN(value), ACOS(value), ATAN(value), ATAN2(y, x) FROM main",
        "SELECT LOG(value), LOG10(value), LN(value), EXP(value) FROM main",
        "SELECT TRUNC(value), TRUNCATE(value, 2) FROM main",
        "SELECT RANDOM(), PI(), DEGREES(angle), RADIANS(angle) FROM main",
        
        # 日期时间函数
        "SELECT NOW(), CURRENT_TIMESTAMP, CURRENT_DATE, CURRENT_TIME FROM main",
        "SELECT EXTRACT(YEAR FROM date_col), DATE_PART('month', date_col) FROM main",
        "SELECT DATE_TRUNC('day', timestamp_col), AGE(date_col) FROM main",
        "SELECT TO_TIMESTAMP(epoch_time), TO_DATE(date_string) FROM main",
        
        # 条件函数
        "SELECT IF(condition, 'true', 'false') FROM main",
        "SELECT DECODE(status, 1, 'active', 2, 'inactive', 'unknown') FROM main",
        "SELECT COALESCE(col1, col2, 'default') FROM main",
        "SELECT NULLIF(col1, col2), GREATEST(a, b, c), LEAST(a, b, c) FROM main",
        
        # 类型转换函数
        "SELECT CAST(value AS INTEGER), TO_NUMBER(text_value) FROM main",
        "SELECT TO_BINARY(hex_string) FROM main",
        
        # 炎凰SQL特有函数
        "SELECT TIME_BUCKET('1h', timestamp_col) FROM main",
        "SELECT REGEX_EXTRACT(text, '[0-9]+') FROM main",
        "SELECT REGEX_MATCH(text, '[a-z]+'), REGEX_REPLACE(text, 'old', 'new') FROM main",
        "SELECT IP_TO_COUNTRY(ip), IP_TO_REGION(ip), IP_TO_CITY(ip) FROM main",
        "SELECT GEOHASH(lat, lon), GEOHASH_DECODE(hash) FROM main",
        "SELECT MD5(text), SHA1(text), SHA256(text) FROM main",
        "SELECT BASE64_ENCODE(text), BASE64_DECODE(encoded) FROM main",
        "SELECT URL_ENCODE(text), URL_DECODE(encoded) FROM main",
        "SELECT UUID() FROM main",
        
        # JSON函数
        "SELECT JSON_EXTRACT(json_col, '$.key') FROM main",
        "SELECT JSON_ARRAY_LENGTH(json_array), JSON_OBJECT_KEYS(json_obj) FROM main",
        "SELECT JSON_TYPEOF(json_value), JSON_VALID(json_string) FROM main",
        
        # 数组函数
        "SELECT ARRAY_LENGTH(array_col), ARRAY_APPEND(array_col, 'item') FROM main",
        "SELECT ARRAY_TO_STRING(array_col, ','), STRING_TO_ARRAY(text, ',') FROM main",
    ]
    
    for test in scalar_function_tests:
        try:
            ast = sqlglot.parse_one(test, dialect="yanhuang")
            print(f"✅ {test}")
        except Exception as e:
            print(f"❌ {test} - 错误: {e}")
    
    # === 4. 聚合函数测试 ===
    print("\n4. 聚合函数支持:")
    aggregate_tests = [
        "SELECT COUNT(*), COUNT(DISTINCT field) FROM main",
        "SELECT SUM(value), AVG(value), MIN(value), MAX(value) FROM main",
        "SELECT MAX_STR(text_field), MIN_STR(text_field) FROM main",
        "SELECT STDDEV_POP(value), STDDEV_SAMP(value) FROM main",
        "SELECT VAR_POP(value), VAR_SAMP(value) FROM main",
        "SELECT STRING_AGG(text_field, ',') FROM main GROUP BY category",
        "SELECT QUANTILE_T_DIGEST(value, 0.5) FROM main GROUP BY category",
        "SELECT PERCENTILE(value, 0.9) FROM main GROUP BY category",
        "SELECT APPROX_COUNT_DISTINCT(field), APPROX_MEDIAN(value) FROM main",
        "SELECT PRODUCT(value) FROM main GROUP BY category",
        "SELECT FIRST_VALUE(value), LAST_VALUE(value) FROM main GROUP BY category",
        "SELECT LATEST_VALUE(value), EARLIEST_VALUE(value) FROM main GROUP BY category",
        "SELECT ARRAY_AGG(field), JSON_AGG(field) FROM main GROUP BY category",
    ]
    
    for test in aggregate_tests:
        try:
            ast = sqlglot.parse_one(test, dialect="yanhuang")
            print(f"✅ {test}")
        except Exception as e:
            print(f"❌ {test} - 错误: {e}")
    
    # === 5. 窗口函数测试 ===
    print("\n5. 窗口函数支持:")
    window_tests = [
        "SELECT COUNT(*) OVER (PARTITION BY id ORDER BY time DESC) FROM main",
        "SELECT ROW_NUMBER() OVER (ORDER BY value DESC) FROM main",
        "SELECT RANK() OVER (ORDER BY score), DENSE_RANK() OVER (ORDER BY score) FROM main",
        "SELECT FIRST_VALUE(value) OVER (PARTITION BY group_id ORDER BY time) FROM main",
        "SELECT LAG(value) OVER (ORDER BY time), LEAD(value) OVER (ORDER BY time) FROM main",
        "SELECT SUM(value) OVER (ORDER BY time ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) FROM main",
        "SELECT NTILE(4) OVER (ORDER BY value), PERCENT_RANK() OVER (ORDER BY value) FROM main",
    ]
    
    for test in window_tests:
        try:
            ast = sqlglot.parse_one(test, dialect="yanhuang")
            print(f"✅ {test}")
        except Exception as e:
            print(f"❌ {test} - 错误: {e}")
    
    # === 6. 表函数测试 ===
    print("\n6. 表函数支持:")
    table_function_tests = [
        "SELECT * FROM GENERATE_SERIES(1, 10)",
        "SELECT * FROM GENERATE_SERIES(1, 10, 2)",
        "SELECT * FROM PARSE_JSON(json_string)",
        "SELECT * FROM PARSE_CSV(csv_string)",
        "SELECT * FROM PARSE_REGEX(text, pattern)",
        "SELECT * FROM IP_LOCATION(ip_address)",
        "SELECT * FROM LOAD_CSV('file.csv')",
        "SELECT * FROM UNNEST(array_col)",
        "SELECT * FROM EXPLODE(array_col)",
    ]
    
    for test in table_function_tests:
        try:
            ast = sqlglot.parse_one(test, dialect="yanhuang")
            print(f"✅ {test}")
        except Exception as e:
            print(f"❌ {test} - 错误: {e}")
    
    # === 7. 特殊语法测试 ===
    print("\n7. 特殊语法支持:")
    special_syntax_tests = [
        # CONTAINS函数
        "SELECT * FROM main WHERE CONTAINS('keyword')",
        "SELECT * FROM main WHERE CONTAINS(field, 'value', FALSE)",
        
        # APPLY算子
        "SELECT * FROM main OUTER APPLY IP_LOCATION(main.ip) ip_table",
        "SELECT * FROM main APPLY (SELECT UPPER(main.message) AS upper_msg) AS sub",
        
        # COLUMNS功能
        "SELECT COLUMNS('^f[1-4]$') EXCEPT (f1) FROM main",
        "SELECT COLUMNS('f_(.*)') AS \"host_{0}\" FROM main",
        
        # 多表合并
        "SELECT * FROM table1 | table2 | table3",
        
        # PIVOT功能
        "PIVOT cities ON year USING SUM(population) GROUP BY country",
        "PIVOT cities ON year IN (2000, 2020) USING SUM(population) GROUP BY country",
        
        # GROUP BY TIME
        "SELECT _time, COUNT(*) FROM events GROUP BY TIME(span='1h')",
        "SELECT _time, region, SUM(sales) FROM data GROUP BY region, TIME(span='1d', start='2023-01-01')",
        
        # SAMPLE语法
        "SELECT * FROM main SAMPLE ROW (50)",
        "SELECT * FROM main SAMPLE BLOCK (25.5)",
        
        # VALUES语句
        "VALUES (1, 'one'), (2, 'two'), (3, 'three')",
        "VALUES (1, 'one'), (2, 'two') AS t(id, name)",
        
        # SHOW语句
        "SHOW TABLES",
        "SHOW FULL TABLES WHERE engine='event_set'",
        
        # CREATE TABLE ENGINE
        "CREATE TABLE test_table ENGINE=event_set",
        "CREATE TABLE kafka_table ENGINE=kafka WITH (server_url='1.1.1.1', topic='events')",
        
        # DELETE增强语法
        "DELETE FROM main WHERE id > 100 ORDER BY id LIMIT 10",
        
        # DESCRIBE语句
        "DESCRIBE main",
    ]
    
    for test in special_syntax_tests:
        try:
            ast = sqlglot.parse_one(test, dialect="yanhuang")
            print(f"✅ {test}")
        except Exception as e:
            print(f"❌ {test} - 错误: {e}")
    
    # === 8. 复杂查询测试 ===
    print("\n8. 复杂查询支持:")
    complex_tests = [
        # CTE + 窗口函数
        """WITH ranked_data AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY value DESC) AS rn
            FROM main
        )
        SELECT * FROM ranked_data WHERE rn <= 5""",
        
        # JOIN + APPLY + CONTAINS
        """SELECT o.*, c.name, ip_info.country
        FROM orders o 
        INNER JOIN customers c ON o.customer_id = c.id
        OUTER APPLY IP_LOCATION(c.ip_address) ip_info
        WHERE CONTAINS(o.description, 'priority')""",
        
        # 子查询 + EXISTS + IN
        """SELECT * FROM orders 
        WHERE customer_id IN (SELECT id FROM customers WHERE country = 'US')
        AND EXISTS (SELECT 1 FROM order_items WHERE order_id = orders.id)""",
        
        # UNION + ORDER BY + LIMIT
        """SELECT name, 'customer' AS type FROM customers
        UNION ALL
        SELECT name, 'supplier' AS type FROM suppliers
        ORDER BY name
        LIMIT 100""",
    ]
    
    for test in complex_tests:
        try:
            ast = sqlglot.parse_one(test, dialect="yanhuang")
            print(f"✅ 复杂查询测试通过")
        except Exception as e:
            print(f"❌ 复杂查询测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("完整性检查完成")
    print("=" * 60)

if __name__ == "__main__":
    test_completeness() 