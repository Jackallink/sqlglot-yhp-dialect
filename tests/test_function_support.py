#!/usr/bin/env python3
"""
炎凰SQL方言函数支持检查脚本
"""

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

def test_function_support():
    """测试炎凰SQL中函数的支持情况"""
    
    # === 1. 标量函数测试 ===
    print("=" * 50)
    print("标量函数支持情况检查")
    print("=" * 50)
    
    scalar_functions = {
        "字符串函数": [
            "SELECT UPPER('hello') FROM main",
            "SELECT LOWER('HELLO') FROM main", 
            "SELECT SUBSTRING('hello', 1, 3) FROM main",
            "SELECT LENGTH('hello') FROM main",
            "SELECT CHAR_LENGTH('hello') FROM main",
            "SELECT CHARACTER_LENGTH('hello') FROM main",
            "SELECT LEFT('hello', 2) FROM main",
            "SELECT RIGHT('hello', 2) FROM main",
            "SELECT REVERSE('hello') FROM main",
            "SELECT REPEAT('abc', 3) FROM main",
            "SELECT LPAD('123', 5, '0') FROM main",
            "SELECT RPAD('123', 5, '0') FROM main",
            "SELECT POSITION('e' IN 'hello') FROM main",
            "SELECT TRIM(' hello ') FROM main",
            "SELECT LTRIM(' hello') FROM main",
            "SELECT RTRIM('hello ') FROM main",
            "SELECT CONCAT('a', 'b') FROM main",
            "SELECT REPLACE('hello', 'l', 'r') FROM main",
        ],
        "数学函数": [
            "SELECT ABS(-5) FROM main",
            "SELECT CEIL(3.14) FROM main",
            "SELECT CEILING(3.14) FROM main",
            "SELECT FLOOR(3.14) FROM main", 
            "SELECT ROUND(3.14159, 2) FROM main",
            "SELECT SQRT(16) FROM main",
            "SELECT POWER(2, 3) FROM main",
            "SELECT POW(2, 3) FROM main",
            "SELECT MOD(10, 3) FROM main",
            "SELECT SIN(1.57) FROM main",
            "SELECT COS(0) FROM main",
            "SELECT TAN(0.785) FROM main",
            "SELECT ASIN(1) FROM main",
            "SELECT ACOS(1) FROM main", 
            "SELECT ATAN(1) FROM main",
            "SELECT LOG(10) FROM main",
            "SELECT LOG10(100) FROM main",
            "SELECT EXP(1) FROM main",
            "SELECT SIGN(-5) FROM main",
            "SELECT TRUNC(3.14159, 2) FROM main",
            "SELECT GREATEST(1, 2, 3) FROM main",
            "SELECT LEAST(1, 2, 3) FROM main",
        ],
        "条件函数": [
            "SELECT IF(1=1, 'true', 'false') FROM main",
            "SELECT DECODE(1, 1, 'one', 2, 'two', 'other') FROM main",
            "SELECT CASE WHEN 1=1 THEN 'true' ELSE 'false' END FROM main",
            "SELECT COALESCE(NULL, 'default') FROM main",
            "SELECT NULLIF('a', 'a') FROM main",
        ],
        "类型转换函数": [
            "SELECT CAST('123' AS INT) FROM main",
            "SELECT CAST(123 AS STRING) FROM main",
            "SELECT CAST('3.14' AS FLOAT) FROM main",
        ],
        "日期时间函数": [
            "SELECT NOW() FROM main",
            "SELECT CURRENT_TIMESTAMP FROM main",
            "SELECT EXTRACT(YEAR FROM NOW()) FROM main",
            "SELECT DATE_TRUNC('month', NOW()) FROM main",
        ],
        "炎凰SQL特有函数": [
            "SELECT CONTAINS('keyword') FROM main",
            "SELECT TIME_BUCKET('1h', ts) FROM main",
            "SELECT REGEX_EXTRACT('abc123', '[0-9]+') FROM main",
            "SELECT REGEX_MATCH('abc', '[a-z]+') FROM main",
            "SELECT IP_TO_COUNTRY('192.168.1.1') FROM main",
            "SELECT IP_TO_REGION('192.168.1.1') FROM main",
            "SELECT IP_TO_CITY('192.168.1.1') FROM main",
            "SELECT GEOHASH(39.9, 116.4, 8) FROM main",
        ],
        "聚合函数（补充）": [
            "SELECT MAX_STR(name) FROM main",
            "SELECT MIN_STR(name) FROM main", 
            "SELECT STDDEV_POP(value) FROM main",
            "SELECT STDDEV_SAMP(value) FROM main",
            "SELECT VAR_POP(value) FROM main",
            "SELECT VAR_SAMP(value) FROM main",
            "SELECT STRING_AGG(name, ',') FROM main",
            "SELECT QUANTILE_T_DIGEST(value, 0.5) FROM main",
            "SELECT PERCENTILE(value, 0.5) FROM main",
            "SELECT APPROX_COUNT_DISTINCT(id) FROM main",
            "SELECT APPROX_MEDIAN(value) FROM main",
            "SELECT PRODUCT(value) FROM main",
            "SELECT LATEST_VALUE(name) FROM main",
            "SELECT EARLIEST_VALUE(name) FROM main",
        ]
    }
    
    total_tests = 0
    passed_tests = 0
    
    for category, functions in scalar_functions.items():
        print(f"\n### {category} ###")
        for sql in functions:
            total_tests += 1
            try:
                ast = sqlglot.parse(sql, dialect='yanhuang')[0]
                generated = ast.sql(dialect='yanhuang')
                print(f"✅ {sql}")
                print(f"   -> {generated}")
                passed_tests += 1
            except Exception as e:
                print(f"❌ {sql}")
                print(f"   错误: {e}")
            print()
    
    # === 2. 表函数测试 ===
    print("=" * 50)
    print("表函数支持情况检查")
    print("=" * 50)
    
    table_functions = {
        "基础表函数": [
            "SELECT * FROM GENERATE_SERIES(1, 10)",
            "SELECT * FROM GENERATE_SERIES(1, 10, 2)",
            "SELECT * FROM UNNEST(ARRAY[1, 2, 3])",
        ],
        "炎凰SQL特有表函数": [
            "SELECT * FROM IP_LOCATION('192.168.1.1')",
            "SELECT * FROM PARSE_JSON('{\"key\": \"value\"}')",
            "SELECT * FROM PARSE_CSV('a,b,c')",
            "SELECT * FROM PARSE_REGEX('abc123', '[0-9]+')",
            "SELECT * FROM PARSE_KV('k1=v1&k2=v2', '&', '=')",
            "SELECT * FROM PARSE_XML('<root><item>value</item></root>')",
            "SELECT * FROM GEO_DISTANCE(39.9, 116.4, 40.0, 116.5)",
            "SELECT * FROM LOAD_CSV('/path/to/file.csv')",
            "SELECT * FROM LOAD_JSON('/path/to/file.json')",
            "SELECT * FROM LOAD_PARQUET('/path/to/file.parquet')",
        ]
    }
    
    for category, functions in table_functions.items():
        print(f"\n### {category} ###")
        for sql in functions:
            total_tests += 1
            try:
                ast = sqlglot.parse(sql, dialect='yanhuang')[0]
                generated = ast.sql(dialect='yanhuang')
                print(f"✅ {sql}")
                print(f"   -> {generated}")
                passed_tests += 1
            except Exception as e:
                print(f"❌ {sql}")
                print(f"   错误: {e}")
            print()
    
    # === 3. 不支持的函数测试 ===
    print("=" * 50)
    print("不支持的函数检查")
    print("=" * 50)
    
    unsupported_functions = [
        "SELECT ARRAY_AGG(value) FROM main",  # 数组聚合函数
        "SELECT ARRAY_LENGTH(ARRAY[1,2,3]) FROM main",  # 数组长度函数
        "SELECT JSONB_AGG(value) FROM main",  # JSONB聚合函数
        "SELECT HSTORE('key', 'value') FROM main",  # HSTORE函数
        "SELECT CROSSTAB('SELECT ...') FROM main",  # 交叉表函数
    ]
    
    for sql in unsupported_functions:
        try:
            ast = sqlglot.parse(sql, dialect='yanhuang')[0]
            generated = ast.sql(dialect='yanhuang')
            print(f"⚠️  意外支持: {sql}")
            print(f"   -> {generated}")
        except Exception as e:
            print(f"✅ 正确拒绝: {sql}")
            print(f"   错误: {e}")
        print()
    
    # === 4. 总结 ===
    print("=" * 50)
    print("测试总结")
    print("=" * 50)
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    return total_tests, passed_tests

if __name__ == "__main__":
    test_function_support() 