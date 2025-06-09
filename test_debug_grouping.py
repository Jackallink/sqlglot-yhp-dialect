#!/usr/bin/env python3
"""
调试GROUPING相关的AST结构
"""

import warnings
import sqlglot
from sqlglot.dialects import Postgres, Yanhuang
import sqlglot.expressions as exp

# 测试SQL
sql = "SELECT a, b FROM table1 GROUP BY GROUPING SETS ((a, b), (a), ())"

print("=== PostgreSQL 解析 ===")
try:
    parsed = sqlglot.parse(sql, read="postgres")[0]
    print(f"解析成功: {parsed}")
    print(f"AST类型: {type(parsed)}")
    
    # 直接访问GROUP BY
    if hasattr(parsed, 'args') and 'group' in parsed.args:
        group_by = parsed.args['group']
        print(f"GROUP BY 找到: {group_by}")
        print(f"GROUP BY 类型: {type(group_by)}")
        
        # 显示GROUP BY对象的所有属性
        print(f"GROUP BY args: {group_by.args}")
        print(f"GROUP BY dir: {[attr for attr in dir(group_by) if not attr.startswith('_')]}")
        
        # 检查特定属性
        for attr_name in ['expressions', 'this', 'expression', 'grouping_sets']:
            if hasattr(group_by, attr_name):
                attr_value = getattr(group_by, attr_name)
                print(f"GROUP BY.{attr_name}: {attr_value} (类型: {type(attr_value)})")
                
                # 如果是列表，检查元素
                if hasattr(attr_value, '__iter__') and not isinstance(attr_value, str):
                    try:
                        for i, item in enumerate(attr_value):
                            print(f"  [{i}]: {item} (类型: {type(item)})")
                            if isinstance(item, exp.GroupingSets):
                                print(f"    这是GroupingSets表达式!")
                                if hasattr(item, 'expressions'):
                                    for j, inner in enumerate(item.expressions):
                                        print(f"      内部[{j}]: {inner} (类型: {type(inner)})")
                    except TypeError:
                        pass
        
        # 尝试查找任何包含GroupingSets的地方
        def find_grouping_sets(obj, path=""):
            """递归查找GroupingSets对象"""
            if isinstance(obj, exp.GroupingSets):
                print(f"找到GroupingSets在 {path}: {obj}")
                return [obj]
            
            results = []
            if hasattr(obj, 'args') and isinstance(obj.args, dict):
                for key, value in obj.args.items():
                    if value is not None:
                        results.extend(find_grouping_sets(value, f"{path}.{key}"))
            
            if hasattr(obj, '__iter__') and not isinstance(obj, (str, dict)):
                try:
                    for i, item in enumerate(obj):
                        if item is not None:
                            results.extend(find_grouping_sets(item, f"{path}[{i}]"))
                except TypeError:
                    pass
            
            return results
        
        grouping_sets = find_grouping_sets(group_by, "group_by")
        print(f"找到的GroupingSets数量: {len(grouping_sets)}")
        
        grouping_sets_all = find_grouping_sets(parsed, "parsed")
        print(f"在整个AST中找到的GroupingSets数量: {len(grouping_sets_all)}")
        
    else:
        print("没有找到GROUP BY子句")
    
except Exception as e:
    print(f"解析失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试其他GROUPING语法 ===")
test_sqls = [
    "SELECT a, b FROM table1 GROUP BY ROLLUP(a, b)",
    "SELECT a, b FROM table1 GROUP BY CUBE(a, b)", 
    "SELECT GROUPING(a) FROM table1 GROUP BY a"
]

for test_sql in test_sqls:
    print(f"\n测试SQL: {test_sql}")
    try:
        parsed = sqlglot.parse(test_sql, read="postgres")[0]
        if hasattr(parsed, 'args') and 'group' in parsed.args:
            group_by = parsed.args['group']
            if group_by:
                # 查找特殊表达式
                def find_special_expressions(obj):
                    results = []
                    if isinstance(obj, (exp.GroupingSets, exp.Rollup, exp.Cube)):
                        results.append(obj)
                    if hasattr(obj, 'args') and isinstance(obj.args, dict):
                        for value in obj.args.values():
                            if value is not None:
                                results.extend(find_special_expressions(value))
                    if hasattr(obj, '__iter__') and not isinstance(obj, (str, dict)):
                        try:
                            for item in obj:
                                if item is not None:
                                    results.extend(find_special_expressions(item))
                        except TypeError:
                            pass
                    return results
                
                special_exprs = find_special_expressions(parsed)
                print(f"  找到特殊表达式: {special_exprs}")
                for expr in special_exprs:
                    print(f"    类型: {type(expr)}, 内容: {expr}")
        
        # 测试转换
        result = sqlglot.transpile(test_sql, read="postgres", write="yanhuang")[0]
        print(f"  转换结果: {result}")
        
    except Exception as e:
        print(f"  解析/转换失败: {e}")

print("\n=== 直接使用Yanhuang方言测试 ===")
# 直接使用Yanhuang方言解析和生成
try:
    from sqlglot.dialects.yanhuang import Yanhuang
    
    # 使用Postgres解析器解析
    parsed = sqlglot.parse(sql, read="postgres")[0]
    
    # 使用Yanhuang生成器生成
    generator = Yanhuang.Generator()
    
    # 捕获警告
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = generator.sql(parsed)
        
        print(f"直接转换结果: {result}")
        
        if w:
            print(f"捕获到 {len(w)} 个警告:")
            for warning in w:
                print(f"  - {warning.message}")
        else:
            print("没有捕获到警告")
            
except Exception as e:
    print(f"直接转换失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== transpile接口测试 ===")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    try:
        result = sqlglot.transpile(sql, read="postgres", write="yanhuang")[0]
        print(f"transpile转换结果: {result}")
        
        if w:
            print(f"捕获到 {len(w)} 个警告:")
            for warning in w:
                print(f"  - {warning.message}")
        else:
            print("没有捕获到警告")
            
    except Exception as e:
        print(f"transpile转换失败: {e}")

def debug_ast_structure(sql, read_dialect="postgres"):
    """调试AST结构"""
    print(f"\n=== 调试SQL: {sql} ===")
    
    try:
        # 解析SQL
        parsed = sqlglot.parse_one(sql, read=read_dialect)
        print(f"解析成功: {type(parsed)}")
        
        # 查找Group表达式
        group_expr = None
        for node in parsed.walk():
            if isinstance(node, sqlglot.expressions.Group):
                group_expr = node
                break
        
        if group_expr:
            print(f"找到Group表达式: {type(group_expr)}")
            print(f"Group.args = {group_expr.args}")
            print(f"Group.expressions = {group_expr.expressions}")
            
            # 检查grouping_sets属性
            grouping_sets = group_expr.args.get("grouping_sets")
            if grouping_sets:
                print(f"grouping_sets = {grouping_sets}")
                for i, gs in enumerate(grouping_sets):
                    print(f"  grouping_sets[{i}] = {gs} (type: {type(gs)})")
            else:
                print("grouping_sets = None")
            
            # 检查expressions列表中的内容
            if group_expr.expressions:
                for i, expr in enumerate(group_expr.expressions):
                    print(f"expressions[{i}] = {expr} (type: {type(expr)})")
        else:
            print("❌ 未找到Group表达式")
            
    except Exception as e:
        print(f"❌ 解析失败: {e}")

def main():
    test_cases = [
        "SELECT region, SUM(sales) FROM sales GROUP BY GROUPING SETS ((region), ())",
        "SELECT a, b, SUM(c) FROM t GROUP BY ROLLUP(a, b)",
        "SELECT x, y, COUNT(*) FROM t GROUP BY CUBE(x, y)",
        "SELECT region, GROUPING(region) FROM sales GROUP BY region"
    ]
    
    for sql in test_cases:
        debug_ast_structure(sql)

if __name__ == "__main__":
    main() 