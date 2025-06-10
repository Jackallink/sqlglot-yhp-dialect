#!/usr/bin/env python3

import sqlglot
from sqlglot import expressions as exp

def test_debug_datatype():
    print("=== 调试datatype_sql方法 ===\\n")
    
    # 创建TIMESTAMPTZ DataType表达式
    timestamptz_type = exp.DataType(this=exp.DataType.Type.TIMESTAMPTZ)
    print(f"TIMESTAMPTZ DataType: {timestamptz_type}")
    print(f"Type value: {timestamptz_type.this}")
    print(f"Is TIMESTAMPTZ: {timestamptz_type.this == exp.DataType.Type.TIMESTAMPTZ}")
    
    # 测试生成器
    from sqlglot.dialects.yanhuang import Yanhuang
    generator = Yanhuang.Generator()
    
    print(f"\\nTZ_TO_WITH_TIME_ZONE: {generator.TZ_TO_WITH_TIME_ZONE}")
    print(f"TYPE_MAPPING中的TIMESTAMPTZ: {generator.TYPE_MAPPING.get(exp.DataType.Type.TIMESTAMPTZ)}")
    
    # 测试datatype_sql方法
    result = generator.datatype_sql(timestamptz_type)
    print(f"\\ndatatype_sql结果: {result}")

if __name__ == "__main__":
    test_debug_datatype() 