import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

# 测试不同的别名情况
test_cases = [
    "SELECT 1 AS a",
    "SELECT 1 a", 
    "SELECT 1 AS a, 2 AS b",
    "SELECT 1 a, 2 b",
]

for sql in test_cases:
    print(f"\n--- Testing: {sql} ---")
    # 解析
    parsed = sqlglot.parse_one(sql, dialect="yanhuang")
    print(f"Parsed AST: {parsed}")
    
    # 生成SQL
    generated = parsed.sql(dialect="yanhuang")
    print(f"Generated SQL: {generated}")
    
    # 检查第一个表达式是否有explicit_as标记
    if parsed.expressions and hasattr(parsed.expressions[0], 'args'):
        explicit_as = parsed.expressions[0].args.get('explicit_as', 'not set')
        print(f"explicit_as: {explicit_as}") 