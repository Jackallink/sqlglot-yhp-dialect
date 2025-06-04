#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects import yanhuang

# 解析包含IN子查询的SQL
sql = "SELECT * FROM orders WHERE CustomerID IN (SELECT CustomerID FROM customers)"

try:
    parsed = sqlglot.parse(sql, dialect='yanhuang')[0]
    print('Parsed successfully:', parsed)
    
    # 查找In节点
    def find_in_nodes(node):
        if hasattr(node, '__class__') and 'In' in str(node.__class__):
            print(f'\nFound In: {node}')
            print(f'In type: {type(node)}')
            print(f'In args: {node.args}')
            
            # 检查所有属性
            print('All In attributes:')
            for attr in dir(node):
                if not attr.startswith('_'):
                    try:
                        value = getattr(node, attr)
                        if not callable(value):
                            print(f'  {attr}: {value} (type: {type(value)})')
                    except:
                        pass
        
        for child in node.iter_expressions() if hasattr(node, 'iter_expressions') else []:
            find_in_nodes(child)
    
    find_in_nodes(parsed)
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc() 