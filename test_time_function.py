import sqlglot
from sqlglot.dialects import yanhuang

# 测试GROUP BY TIME()功能
sql = """
SELECT country, COUNT(*)
FROM events
GROUP BY country, TIME(start='1990-01-01T00:00:00', end='2020-01-01T00:00:00', span='5 years')
"""

try:
    ast = sqlglot.parse(sql, dialect=yanhuang.Yanhuang)[0]
    print('解析成功!')
    print('完整AST:')
    print(ast)
    print()
    
    # 检查GROUP BY部分
    group_by = ast.find(sqlglot.expressions.Group)
    if group_by:
        print('GROUP BY表达式:')
        for expr in group_by.expressions:
            print(f'  - {type(expr).__name__}: {expr}')
            if hasattr(expr, 'expressions'):
                print(f'    参数: {expr.expressions}')
                for param in expr.expressions:
                    print(f'      - {type(param).__name__}: {param}')
    
    print()
    print('重新生成SQL:')
    generated = ast.sql(dialect=yanhuang.Yanhuang)
    print(generated)
    
except Exception as e:
    print(f'错误: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc() 