#!/usr/bin/env python3
"""
测试DATABASE函数的具体问题
"""

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang
from sqlglot import UnsupportedError, ParseError

def test_database_function():
    print("🔍 测试DATABASE函数处理")
    
    # 测试各种DATABASE函数的使用方式
    test_cases = [
        "SELECT DATABASE()",
        "SELECT DATABASE() FROM table1",
        "DATABASE()",
        "DATABASE",
    ]
    
    for sql in test_cases:
        print(f"\n📝 测试SQL: {sql}")
        try:
            parsed = sqlglot.parse_one(sql, dialect="yanhuang")
            print(f"✅ 解析成功: {parsed}")
            result = parsed.sql(dialect=Yanhuang)
            print(f"✅ 生成成功: {result}")
        except UnsupportedError as e:
            print(f"✅ 预期的UnsupportedError: {e}")
        except ParseError as e:
            print(f"❌ 解析错误: {e}")
        except Exception as e:
            print(f"❌ 意外错误: {type(e).__name__}: {e}")
    
    # 测试具体的解析器行为
    print(f"\n🔧 调试解析器行为:")
    try:
        # 创建解析器实例
        parser = Yanhuang.Parser()
        
        # 检查NO_PAREN_FUNCTION_PARSERS
        print(f"DATABASE在NO_PAREN_FUNCTION_PARSERS中: {'DATABASE' in parser.NO_PAREN_FUNCTION_PARSERS}")
        print(f"DATABASE在FUNCTIONS中: {'DATABASE' in parser.FUNCTIONS}")
        
        # 手动测试解析
        parser._reset("DATABASE()")
        print(f"当前token: {parser._curr}")
        
        # 测试NO_PAREN解析
        if 'DATABASE' in parser.NO_PAREN_FUNCTION_PARSERS:
            try:
                result = parser.NO_PAREN_FUNCTION_PARSERS['DATABASE'](parser)
                print(f"NO_PAREN解析结果: {result}")
            except Exception as e:
                print(f"NO_PAREN解析错误: {type(e).__name__}: {e}")
        
    except Exception as e:
        print(f"❌ 解析器调试错误: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_database_function() 