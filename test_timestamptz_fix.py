#!/usr/bin/env python3

import sqlglot

def test_timestamptz_fix():
    print("=== TIMESTAMPTZ修正验证 ===\\n")
    
    test_cases = [
        "SELECT TIMESTAMPTZ '2024-01-01T00:00:00+08:00' as ts",
        "SELECT CAST('2024-01-01T00:00:00+08:00' AS TIMESTAMPTZ) as ts",
        "SELECT '2024-01-01T00:00:00+08:00'::TIMESTAMPTZ as ts"
    ]
    
    for sql in test_cases:
        try:
            result = sqlglot.transpile(sql, read='postgres', write='yanhuang')[0]
            print(f"输入: {sql}")
            print(f"输出: {result}")
            print()
        except Exception as e:
            print(f"错误: {sql} -> {e}")
            print()

if __name__ == "__main__":
    test_timestamptz_fix() 