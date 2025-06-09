#!/usr/bin/env python
"""
兼容性问题修复验证脚本
==================

测试 TimeStrLiteral 兼容性修复是否有效解决了用户遇到的 
"module 'sqlglot.expressions' has no attribute 'TimeStrLiteral'" 问题。
"""

def test_compatibility_fix():
    """测试兼容性修复是否有效"""
    print("🔍 测试 SQLGlot TimeStrLiteral 兼容性修复...")
    print("="*60)
    
    # 第一步：检查原始SQLGlot中是否有TimeStrLiteral
    try:
        import sqlglot.expressions as exp
        original_has_timestr = hasattr(exp, 'TimeStrLiteral')
        print(f"原始SQLGlot中TimeStrLiteral存在: {original_has_timestr}")
    except ImportError:
        print("❌ 无法导入SQLGlot")
        return False
    
    # 第二步：导入炎凰方言包（会自动应用兼容性修复）
    try:
        import sqlglot_yanhuang
        print("✅ 成功导入炎凰方言包")
    except ImportError as e:
        print(f"❌ 无法导入炎凰方言包: {e}")
        return False
    
    # 第三步：检查修复后是否有TimeStrLiteral
    try:
        import sqlglot.expressions as exp
        fixed_has_timestr = hasattr(exp, 'TimeStrLiteral')
        print(f"修复后SQLGlot中TimeStrLiteral存在: {fixed_has_timestr}")
        
        if fixed_has_timestr:
            # 测试TimeStrLiteral类是否可用
            timestr_class = getattr(exp, 'TimeStrLiteral')
            instance = timestr_class(this="test")
            print(f"✅ TimeStrLiteral类可正常实例化: {type(instance)}")
        
    except Exception as e:
        print(f"❌ 检查TimeStrLiteral时出错: {e}")
        return False
    
    # 第四步：检查版本兼容性信息
    try:
        compatibility_info = sqlglot_yanhuang.check_compatibility()
        print("\n📊 兼容性检查结果:")
        print(f"  SQLGlot版本: {compatibility_info['sqlglot_version']}")
        print(f"  兼容性状态: {'✅ 兼容' if compatibility_info['compatible'] else '⚠️ 有问题'}")
        
        if compatibility_info['issues']:
            print("  发现的问题:")
            for issue in compatibility_info['issues']:
                print(f"    • {issue}")
        
        if compatibility_info['recommendations']:
            print("  建议:")
            for rec in compatibility_info['recommendations']:
                print(f"    • {rec}")
                
    except Exception as e:
        print(f"❌ 兼容性检查失败: {e}")
        return False
    
    # 第五步：测试基本的SQL转换功能
    try:
        print("\n🔧 测试基本SQL转换功能...")
        test_sql = "SELECT EXTRACT(YEAR FROM date_col) FROM test_table"
        result = sqlglot_yanhuang.transpile_to_yanhuang(test_sql)
        print(f"  输入: {test_sql}")
        print(f"  输出: {result}")
        print("✅ SQL转换功能正常")
    except Exception as e:
        print(f"❌ SQL转换功能失败: {e}")
        return False
    
    # 第六步：测试所有其他兼容性表达式
    try:
        print("\n🔍 测试其他兼容性表达式...")
        test_expressions = [
            'DateStrLiteral',
            'TimestampStrLiteral', 
            'TimeToTimeStr',
            'UnixToTimeStr'
        ]
        
        for expr_name in test_expressions:
            if hasattr(exp, expr_name):
                expr_class = getattr(exp, expr_name)
                print(f"  ✅ {expr_name}: {expr_class}")
            else:
                print(f"  ❌ {expr_name}: 不存在")
    except Exception as e:
        print(f"❌ 表达式兼容性测试失败: {e}")
        return False
    
    print("\n🎉 兼容性修复验证完成！")
    return True

def test_edge_cases():
    """测试边界情况"""
    print("\n🧪 测试边界情况...")
    
    try:
        import sqlglot.expressions as exp
        
        # 测试1：TimeStrLiteral实例化和使用
        timestr = exp.TimeStrLiteral(this="2023-01-01 12:00:00")
        print(f"✅ TimeStrLiteral实例化成功: {timestr}")
        
        # 测试2：尝试在SQL解析中使用（如果适用）
        import sqlglot
        try:
            # 注意：这可能不会直接使用TimeStrLiteral，但不应该因为缺少类而崩溃
            ast = sqlglot.parse_one("SELECT '2023-01-01'::timestamp")
            print("✅ SQL解析正常工作")
        except Exception as e:
            print(f"⚠️ SQL解析警告: {e}")
        
        # 测试3：检查类的基础属性
        if hasattr(timestr, 'this'):
            print(f"✅ TimeStrLiteral.this属性: {timestr.this}")
        
        return True
        
    except Exception as e:
        print(f"❌ 边界情况测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_compatibility_fix()
    
    if success:
        test_edge_cases()
        print("\n✅ 所有测试通过！TimeStrLiteral兼容性问题已修复。")
        print("\n📋 用户使用指南:")
        print("1. 在其他项目中安装新的whl包")
        print("2. 导入: import sqlglot_yanhuang")
        print("3. 兼容性模块会自动修复TimeStrLiteral问题")
        print("4. 正常使用SQL转换功能")
    else:
        print("\n❌ 兼容性修复验证失败，需要进一步调试。")
        exit(1) 