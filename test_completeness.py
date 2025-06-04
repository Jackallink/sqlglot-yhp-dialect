#!/usr/bin/env python3
"""
炎凰SQL方言完整性测试
"""

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

def test_completeness():
    """测试炎凰SQL方言的完整性"""
    
    test_sqls = [
        # Unicode字符串测试
        "SELECT U&'\\0061bcd' AS field_name FROM main LIMIT 1",
        "SELECT U&'!0061bcd!!' UESCAPE '!' AS field_name FROM main LIMIT 1",
        
        # E前缀字符串测试
        "SELECT E'abc\\ndef\\gh' AS field_name FROM main LIMIT 1",
        
        # COLUMNS语法测试
        "SELECT COLUMNS('^f[1-4]$') EXCEPT (f1) FROM main",
        "SELECT COLUMNS('^f[1-4]$') REPLACE (f2+1 AS f2) FROM main",
        "SELECT COLUMNS('f_(.*)') AS 'host_{0}' FROM tbl",
        "SELECT * EXCEPT(request_service) REPLACE (lower(request_method) AS request_method) FROM main",
        
        # PIVOT测试
        "PIVOT cities ON year USING SUM(population) GROUP BY country ORDER BY country DESC",
        "PIVOT cities ON year IN (2000, 2020) USING SUM(population) GROUP BY country",
        
        # APPLY测试
        "SELECT * FROM main OUTER APPLY ip_location(main.ip) ip_table",
        "SELECT * FROM main APPLY (SELECT UPPER(main._message) AS upper_message) AS table_bar",
        
        # 炎凰SQL特有函数
        "SELECT TIME_BUCKET('1h', _time) FROM main",
        "SELECT REGEX_EXTRACT(message, '(\\d+)') FROM main",
        "SELECT IP_TO_COUNTRY(ip) FROM main",
        "SELECT GEOHASH(lat, lon) FROM main",
        "SELECT UUID() FROM main",
        "SELECT MD5(message) FROM main",
        "SELECT BASE64_ENCODE(data) FROM main",
        
        # 窗口函数
        "SELECT ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY _time) FROM main",
        "SELECT LAG(price, 1) OVER (ORDER BY _time) FROM main",
        
        # 聚合函数
        "SELECT STRING_AGG(name, ',') FROM main GROUP BY category",
        "SELECT APPROX_COUNT_DISTINCT(user_id) FROM main",
        "SELECT QUANTILE_T_DIGEST(price, 0.5) FROM main GROUP BY category",
        
        # 表函数
        "SELECT * FROM PARSE_JSON(data) AS t",
        "SELECT * FROM GENERATE_SERIES(1, 10) AS t",
        
        # DELETE增强语法
        "DELETE FROM main WHERE CONTAINS('password') ORDER BY _time LIMIT 1",
        
        # VALUES语句
        "VALUES (1, 'one'), (2, 'two') AS t(id, name)",
        
        # SHOW语句
        "SHOW FULL TABLES WHERE table_name LIKE 'test%'",
        
        # CREATE TABLE
        "CREATE TABLE test ENGINE=event_set",
        "CREATE TABLE kafka_table ENGINE=kafka WITH (server_url='localhost', topic='events')",
        
        # 多表合并语法
        "SELECT * FROM table1 | table2 | table3",
        
        # GROUP BY TIME语法
        "SELECT COUNT(*) FROM main GROUP BY TIME(span='1h', start='2023-01-01')",
        
        # SAMPLE语法
        "SELECT * FROM main SAMPLE ROW (10)",
        
        # CONTAINS函数
        "SELECT * FROM main WHERE CONTAINS('keyword')",
        "SELECT * FROM main WHERE CONTAINS(field, 'keyword', false)",
        
        # DECODE函数
        "SELECT DECODE(status, '200', 'OK', '404', 'Not Found', 'Unknown') FROM main",
        
        # 条件函数
        "SELECT IF(score > 80, 'Pass', 'Fail') FROM main",
        "SELECT GREATEST(a, b, c) FROM main",
        "SELECT NULLIF(value, 0) FROM main",
        
        # 类型转换
        "SELECT TO_NUMBER(str_value) FROM main",
        "SELECT CAST(value AS VARBINARY) FROM main",
        
        # 复杂嵌套
        "WITH cte AS (SELECT * FROM main WHERE CONTAINS('error')) SELECT COUNT(*) FROM cte",
        
        # 窗口函数运算（应该自动转换为子查询）
        "SELECT user_id, COUNT(*) OVER() + 1 FROM main",
        
        # CTE
        "WITH t1 AS (SELECT * FROM main), t2 AS (SELECT * FROM t1) SELECT * FROM t2",
    ]

    success_count = 0
    failed_sqls = []

    print("=== 炎凰SQL方言完整性测试 ===\n")

    for i, sql in enumerate(test_sqls, 1):
        try:
            parsed = sqlglot.parse_one(sql, dialect='yanhuang')
            regenerated = parsed.sql(dialect='yanhuang')
            print(f"✅ [{i:2d}] {sql[:60]}...")
            success_count += 1
        except Exception as e:
            print(f"❌ [{i:2d}] {sql[:60]}... - {str(e)[:80]}")
            failed_sqls.append((sql, str(e)))

    print(f"\n=== 测试结果 ===")
    print(f"总计: {len(test_sqls)}个测试")
    print(f"成功: {success_count}个")
    print(f"失败: {len(failed_sqls)}个")
    print(f"成功率: {success_count/len(test_sqls)*100:.1f}%")

    if failed_sqls:
        print("\n=== 失败的SQL语句 ===")
        for sql, error in failed_sqls:
            print(f"SQL: {sql}")
            print(f"错误: {error}")
            print()

if __name__ == "__main__":
    test_completeness() 