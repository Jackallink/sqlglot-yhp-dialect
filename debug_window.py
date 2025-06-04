#!/usr/bin/env python3

import sqlglot
from sqlglot.dialects import yanhuang

# 解析包含RANGE框架的SQL
sql = 'SELECT SUM(size) OVER (ORDER BY time RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) FROM main'

try:
    parsed = sqlglot.parse(sql, dialect='yanhuang')[0]
    print('Parsed successfully:', parsed)
    
    # 查找Window节点
    def find_windows(node):
        if hasattr(node, '__class__') and 'Window' in str(node.__class__):
            print(f'\nFound Window: {node}')
            print(f'Window type: {type(node)}')
            print(f'Window args: {node.args}')
            
            if 'spec' in node.args:
                spec = node.args['spec']
                print(f'Spec: {spec}')
                print(f'Spec type: {type(spec)}')
                print(f'Spec args: {spec.args if hasattr(spec, "args") else "No args"}')
                
                if hasattr(spec, 'kind'):
                    print(f'Spec kind: {spec.kind}')
                    print(f'Spec kind type: {type(spec.kind)}')
                else:
                    print('No kind attribute')
                    
                # 检查所有属性
                print('All spec attributes:')
                for attr in dir(spec):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(spec, attr)
                            if not callable(value):
                                print(f'  {attr}: {value} (type: {type(value)})')
                        except:
                            pass
        
        for child in node.iter_expressions() if hasattr(node, 'iter_expressions') else []:
            find_windows(child)
    
    find_windows(parsed)
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc() 