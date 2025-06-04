#!/usr/bin/env python3
"""
炎凰SQL字符串转义功能演示

展示E前缀（C-style转义）和U&前缀（Unicode编码）字符串的解析和生成功能。
"""

import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

def demo_string_escapes():
    """演示字符串转义功能"""
    
    print("🔥 炎凰SQL字符串转义功能演示")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        # E前缀字符串（C-style转义）
        ("E前缀字符串 - 换行符", "SELECT E'line1\\nline2' AS multiline FROM main"),
        ("E前缀字符串 - 制表符", "SELECT E'hello\\tworld' AS greeting FROM main"),
        ("E前缀字符串 - 回车符", "SELECT E'first\\rsecond' AS text FROM main"),
        ("E前缀字符串 - 混合转义", "SELECT E'abc\\ndef\\tghi' AS mixed FROM main"),
        
        # U&前缀字符串（Unicode编码）
        ("U&前缀字符串 - 基本Unicode", "SELECT U&'\\0061bcd' AS unicode_text FROM main"),
        ("U&前缀字符串 - 复杂Unicode", "SELECT U&'Hello \\2603 winter!' AS snowman FROM main"),
        ("U&前缀字符串 - 带UESCAPE", "SELECT U&'!0061bcd!!' UESCAPE '!' AS custom_escape FROM main"),
        ("U&前缀字符串 - 自定义转义符", "SELECT U&'Hello #2603 world' UESCAPE '#' AS hash_escape FROM main"),
        
        # 普通字符串（对比）
        ("普通字符串", "SELECT 'normal string' AS normal FROM main"),
        ("转义单引号", "SELECT 'tom''s cat' AS escaped FROM main"),
    ]
    
    for description, sql in test_cases:
        print(f"\n📝 {description}")
        print(f"输入: {sql}")
        
        try:
            # 解析SQL
            parsed = sqlglot.parse_one(sql, dialect="yanhuang")
            print(f"解析: ✅ 成功")
            
            # 生成SQL
            generated = parsed.sql(dialect="yanhuang")
            print(f"输出: {generated}")
            
            # 显示AST中的字符串类型
            for node in parsed.walk():
                if hasattr(node, 'this') and isinstance(node.this, str):
                    node_type = type(node).__name__
                    if node_type in ['ByteString', 'UnicodeString', 'Literal']:
                        print(f"类型: {node_type}")
                        if hasattr(node, 'escape') and node.escape:
                            print(f"转义: {node.escape}")
                        break
            
        except Exception as e:
            print(f"解析: ❌ 失败 - {e}")
        
        print("-" * 40)

def demo_string_escape_comparison():
    """演示不同方言的字符串转义差异"""
    
    print("\n🔄 字符串转义方言对比")
    print("=" * 50)
    
    test_sql = "SELECT E'hello\\nworld' AS greeting FROM main"
    dialects = ["yanhuang", "postgres", "mysql", "sqlite"]
    
    print(f"原始SQL: {test_sql}")
    print()
    
    for dialect in dialects:
        try:
            parsed = sqlglot.parse_one(test_sql, dialect=dialect)
            generated = parsed.sql(dialect=dialect)
            print(f"{dialect:>10}: {generated}")
        except Exception as e:
            print(f"{dialect:>10}: ❌ 不支持 - {e}")

if __name__ == "__main__":
    demo_string_escapes()
    demo_string_escape_comparison()
    
    print("\n✨ 字符串转义功能演示完成！")
    print("\n📋 功能总结:")
    print("✅ E前缀字符串 - 支持C-style转义字符 (\\n, \\t, \\r, \\b, \\f)")
    print("✅ U&前缀字符串 - 支持Unicode编码 (\\xxxx, \\+xxxxxx)")
    print("✅ UESCAPE关键字 - 支持自定义转义标识符")
    print("✅ 普通字符串 - 保持标准SQL兼容性")
    print("✅ 完整的解析和生成支持") 