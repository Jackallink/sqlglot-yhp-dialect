#!/usr/bin/env python3
import sqlglot

# 只测试之前失败的PIVOT语句
sql = 'PIVOT cities ON year USING SUM(population) GROUP BY country ORDER BY country DESC'
try:
    parsed = sqlglot.parse_one(sql, dialect='yanhuang')
    regenerated = parsed.sql(dialect='yanhuang')
    print(f'✅ 修复成功！')
    print(f'原SQL: {sql}')
    print(f'重生成: {regenerated}')
except Exception as e:
    print(f'❌ 仍然失败: {e}') 