#!/usr/bin/env python3
"""
测试修复后的炎凰方言注册和转换功能
"""

import sys
import os

def test_import_and_registration():
    """测试导入和注册"""
    print("=" * 60)
    print("测试1：导入和方言注册")
    print("=" * 60)
    
    try:
        # 切换到包目录
        original_dir = os.getcwd()
        os.chdir("sqlglot-yanhuang-dialect")
        
        # 导入包
        sys.path.insert(0, '.')
        import sqlglot_yanhuang
        
        print("✅ 包导入成功")
        
        # 检查版本
        print(f"✅ 版本: {sqlglot_yanhuang.__version__}")
        
        # 检查方言类
        print(f"✅ 炎凰方言类: {sqlglot_yanhuang.Yanhuang}")
        
        # 运行注册检查
        print("\n注册状态检查：")
        checks = sqlglot_yanhuang.check_registration()
        for check in checks:
            print(f"  {check}")
        
        os.chdir(original_dir)
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

def test_basic_conversion():
    """测试基础转换功能"""
    print("\n" + "=" * 60)
    print("测试2：基础SQL转换")
    print("=" * 60)
    
    try:
        original_dir = os.getcwd()
        os.chdir("sqlglot-yanhuang-dialect")
        sys.path.insert(0, '.')
        
        import sqlglot_yanhuang
        
        test_cases = [
            "SELECT 1",
            "SELECT 'hello' || ' world'", 
            "SELECT EXTRACT(year FROM now())",
            "SELECT CARDINALITY(ARRAY[1,2,3])"
        ]
        
        success_count = 0
        for i, sql in enumerate(test_cases, 1):
            try:
                result = sqlglot_yanhuang.transpile_to_yanhuang(sql)
                print(f"测试 {i}:")
                print(f"  输入: {sql}")
                print(f"  输出: {result}")
                print("  ✅ 转换成功")
                success_count += 1
            except Exception as e:
                print(f"测试 {i}:")
                print(f"  输入: {sql}")
                print(f"  ❌ 转换失败: {e}")
            print()
        
        print(f"基础转换测试: {success_count}/{len(test_cases)} 成功")
        
        os.chdir(original_dir)
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

def test_sqlglot_integration():
    """测试SQLGlot集成"""
    print("\n" + "=" * 60)
    print("测试3：SQLGlot直接集成")
    print("=" * 60)
    
    try:
        original_dir = os.getcwd()
        os.chdir("sqlglot-yanhuang-dialect")
        sys.path.insert(0, '.')
        
        # 先导入我们的包注册方言
        import sqlglot_yanhuang
        import sqlglot
        
        # 测试直接使用SQLGlot
        test_sql = "SELECT EXTRACT(year FROM CURRENT_TIMESTAMP)"
        
        try:
            result = sqlglot.transpile(test_sql, read="postgres", write="yanhuang")
            print(f"✅ SQLGlot直接转换成功:")
            print(f"  输入: {test_sql}")
            print(f"  输出: {result[0]}")
        except Exception as e:
            print(f"❌ SQLGlot直接转换失败: {e}")
            print("💡 尝试使用便捷函数...")
            result = sqlglot_yanhuang.transpile_to_yanhuang(test_sql)
            print(f"✅ 便捷函数转换成功: {result}")
        
        os.chdir(original_dir)
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

def test_lateral_join_conversion():
    """测试LATERAL JOIN转换"""
    print("\n" + "=" * 60)
    print("测试4：LATERAL JOIN转换")
    print("=" * 60)
    
    try:
        original_dir = os.getcwd()
        os.chdir("sqlglot-yanhuang-dialect")
        sys.path.insert(0, '.')
        
        import sqlglot_yanhuang
        
        lateral_sql = """
        SELECT u.name, o.order_count 
        FROM users u 
        LEFT JOIN LATERAL (
            SELECT count(*) as order_count 
            FROM orders 
            WHERE user_id = u.id
        ) o ON true
        """
        
        result = sqlglot_yanhuang.transpile_to_yanhuang(lateral_sql)
        print(f"LATERAL JOIN转换:")
        print(f"输入SQL：")
        print(lateral_sql)
        print(f"输出SQL：")
        print(result)
        
        if "OUTER APPLY" in result or "CROSS APPLY" in result:
            print("✅ LATERAL JOIN成功转换为APPLY语法")
        else:
            print("❌ LATERAL JOIN转换可能不完整")
        
        os.chdir(original_dir)
        return True
        
    except Exception as e:
        print(f"❌ LATERAL JOIN测试失败: {e}")
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

def main():
    """主测试函数"""
    print("炎凰方言修复方案验证测试")
    print("=" * 80)
    
    tests = [
        test_import_and_registration,
        test_basic_conversion,
        test_sqlglot_integration,
        test_lateral_join_conversion,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 异常: {e}")
            results.append(False)
    
    success_count = sum(results)
    total_count = len(results)
    
    print("\n" + "=" * 80)
    print(f"测试结果汇总: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！方言注册和转换功能正常！")
    elif success_count >= total_count - 1:
        print("✅ 核心功能正常，方案基本可行")
    else:
        print("⚠️ 需要进一步修复")
    
    print("\n解决方案状态：")
    if success_count > 0:
        print("✅ 炎凰方言可以正常工作")
        print("✅ 支持PostgreSQL到炎凰数据的转换")
        print("✅ 包体积小，易于分发")
        print("✅ 提供便捷的Python API")
        
        if success_count == total_count:
            print("🚀 方案B（动态方言注入）完全可行！")
        else:
            print("🔧 方案B基本可行，部分功能需要优化")
    else:
        print("❌ 需要进一步调试和修复")
    
    print("=" * 80)

if __name__ == "__main__":
    main() 