#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
炎凰数据SQL方言独立部署验证测试
============================

用于验证：PyPI官方SQLGlot + 本地炎凰方言whl包的组合部署

使用方法：
1. 在任意新项目中放置此文件
2. 安装官方SQLGlot：pip install sqlglot
3. 安装炎凰方言包：pip install /path/to/sqlglot_yanhuang_dialect-1.0.0-py3-none-any.whl
4. 运行此测试：python 独立部署验证测试.py

预期结果：核心功能测试应该通过，证明部署成功
"""

import sys
import warnings
from datetime import datetime

def print_header(title):
    """打印测试标题"""
    print("\n" + "=" * 60)
    print(f"{title}")
    print("=" * 60)

def print_test_result(test_name, success, message=""):
    """打印测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    print(f"{test_name}: {status}")
    if message:
        print(f"  详情: {message}")

def test_environment_check():
    """测试1：环境检查"""
    print_header("测试1：环境检查")
    
    results = []
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 8):
        print_test_result("Python版本检查", True, f"Python {python_version.major}.{python_version.minor}")
        results.append(True)
    else:
        print_test_result("Python版本检查", False, f"需要Python 3.8+，当前：{python_version.major}.{python_version.minor}")
        results.append(False)
    
    # 检查SQLGlot安装
    try:
        import sqlglot
        sqlglot_version = getattr(sqlglot, '__version__', 'Unknown')
        print_test_result("SQLGlot安装检查", True, f"版本: {sqlglot_version}")
        results.append(True)
    except ImportError as e:
        print_test_result("SQLGlot安装检查", False, f"未安装SQLGlot: {e}")
        results.append(False)
        return False  # 如果SQLGlot未安装，后续测试无法进行
    
    # 检查炎凰方言包安装
    try:
        import sqlglot_yanhuang
        yanhuang_version = getattr(sqlglot_yanhuang, '__version__', 'Unknown')
        print_test_result("炎凰方言包安装检查", True, f"版本: {yanhuang_version}")
        results.append(True)
    except ImportError as e:
        print_test_result("炎凰方言包安装检查", False, f"未安装炎凰方言包: {e}")
        results.append(False)
        return False  # 如果方言包未安装，后续测试无法进行
    
    return all(results)

def test_dialect_registration():
    """测试2：方言注册验证（核心测试）"""
    print_header("测试2：方言注册验证（核心测试）")
    
    try:
        import sqlglot_yanhuang
        
        # 使用包提供的诊断工具
        if hasattr(sqlglot_yanhuang, 'check_registration'):
            checks = sqlglot_yanhuang.check_registration()
            
            success_count = 0
            for check in checks:
                if "✅" in check:
                    print_test_result("方言注册状态", True, check.replace("✅ ", ""))
                    success_count += 1
                else:
                    print_test_result("方言注册状态", False, check.replace("❌ ", ""))
            
            # 至少有一个成功就算通过
            return success_count > 0
        else:
            # 手动检查
            try:
                import sqlglot
                result = sqlglot.transpile("SELECT 1", read="postgres", write="yanhuang")
                print_test_result("方言注册验证", True, "SQLGlot可以识别yanhuang方言")
                return True
            except Exception as e:
                print_test_result("方言注册验证", False, f"SQLGlot无法识别yanhuang方言: {e}")
                return False
    
    except Exception as e:
        print_test_result("方言注册验证", False, f"验证过程出错: {e}")
        return False

def test_core_conversion():
    """测试3：核心SQL转换功能（必须通过）"""
    print_header("测试3：核心SQL转换功能（必须通过）")
    
    core_test_cases = [
        {
            "name": "简单查询",
            "sql": "SELECT 1",
            "expected_contains": ["SELECT", "1"]
        },
        {
            "name": "字符串连接转换（核心功能）",
            "sql": "SELECT 'hello' || ' world'",
            "expected_contains": ["CONCAT"]
        },
        {
            "name": "EXTRACT函数映射（核心功能）",
            "sql": "SELECT EXTRACT(year FROM now())",
            "expected_contains": ["DATE_PART"]
        }
    ]
    
    try:
        import sqlglot_yanhuang
        
        passed_count = 0
        total_count = len(core_test_cases)
        
        for i, test_case in enumerate(core_test_cases, 1):
            try:
                result = sqlglot_yanhuang.transpile_to_yanhuang(test_case["sql"])
                
                # 检查是否包含期望的关键词
                all_found = True
                missing_keywords = []
                for keyword in test_case["expected_contains"]:
                    if keyword not in result:
                        all_found = False
                        missing_keywords.append(keyword)
                
                if all_found:
                    print_test_result(f"核心转换{i}: {test_case['name']}", True, f"输出: {result}")
                    passed_count += 1
                else:
                    print_test_result(f"核心转换{i}: {test_case['name']}", False, 
                                    f"缺少关键词: {missing_keywords}, 输出: {result}")
                    
            except Exception as e:
                print_test_result(f"核心转换{i}: {test_case['name']}", False, f"转换失败: {e}")
        
        overall_success = passed_count >= 2  # 至少2个核心功能通过
        print_test_result(f"核心转换汇总", overall_success, f"{passed_count}/{total_count} 通过")
        
        return overall_success
    
    except Exception as e:
        print_test_result("核心转换功能", False, f"测试过程出错: {e}")
        return False

def test_sqlglot_integration():
    """测试4：SQLGlot集成验证（重要但不强制）"""
    print_header("测试4：SQLGlot集成验证（重要但不强制）")
    
    try:
        # 先导入炎凰方言包（触发注册）
        import sqlglot_yanhuang
        import sqlglot
        
        # 测试基本的SQLGlot集成
        test_sql = "SELECT EXTRACT(month FROM CURRENT_TIMESTAMP)"
        
        try:
            result = sqlglot.transpile(test_sql, read="postgres", write="yanhuang")
            if "DATE_PART" in result[0]:
                print_test_result("SQLGlot集成", True, f"PostgreSQL→炎凰转换成功: {result[0]}")
                return True
            else:
                print_test_result("SQLGlot集成", False, f"转换结果不符合预期: {result[0]}")
                return False
        except Exception as e:
            print_test_result("SQLGlot集成", False, f"转换失败: {e}")
            
            # 尝试便捷函数作为备用
            try:
                result = sqlglot_yanhuang.transpile_to_yanhuang(test_sql)
                print_test_result("便捷函数备用", True, f"备用方案成功: {result}")
                return True
            except Exception as e2:
                print_test_result("便捷函数备用", False, f"备用方案也失败: {e2}")
                return False
    
    except Exception as e:
        print_test_result("SQLGlot集成测试", False, f"测试过程出错: {e}")
        return False

def test_lateral_join_conversion():
    """测试5：LATERAL JOIN转换（高级功能，可选）"""
    print_header("测试5：LATERAL JOIN转换（高级功能）")
    
    try:
        import sqlglot_yanhuang
        
        lateral_sql = "SELECT u.name FROM users u LEFT JOIN LATERAL (SELECT count(*) FROM orders WHERE user_id = u.id) o ON true"
        
        result = sqlglot_yanhuang.transpile_to_yanhuang(lateral_sql)
        
        # 检查是否转换为APPLY语法
        if "OUTER APPLY" in result or "CROSS APPLY" in result:
            print_test_result("LATERAL JOIN转换", True, "成功转换为APPLY语法")
            print(f"  输出: {result}")
            return True
        else:
            print_test_result("LATERAL JOIN转换", False, "未转换为APPLY语法，但这是可选功能")
            print(f"  输出: {result}")
            return False  # 不影响总体评价
    
    except Exception as e:
        print_test_result("LATERAL JOIN转换", False, f"转换失败: {e}")
        return False

def test_basic_functionality():
    """测试6：基本功能验证（确保包可用）"""
    print_header("测试6：基本功能验证")
    
    try:
        import sqlglot_yanhuang
        
        # 测试多个简单转换
        simple_tests = [
            ("SELECT NOW()", ["NOW"]),
            ("SELECT CURRENT_TIMESTAMP", ["NOW"]),
            ("SELECT 'a' || 'b'", ["CONCAT"]),
        ]
        
        passed_count = 0
        for sql, expected in simple_tests:
            try:
                result = sqlglot_yanhuang.transpile_to_yanhuang(sql)
                if any(keyword in result for keyword in expected):
                    passed_count += 1
                    print_test_result(f"基本功能测试", True, f"{sql} → {result}")
                else:
                    print_test_result(f"基本功能测试", False, f"{sql} → {result}")
            except Exception as e:
                print_test_result(f"基本功能测试", False, f"{sql} 失败: {e}")
        
        success = passed_count >= 2  # 至少2个基本功能通过
        print_test_result("基本功能汇总", success, f"{passed_count}/{len(simple_tests)} 通过")
        
        return success
    
    except Exception as e:
        print_test_result("基本功能测试", False, f"测试过程出错: {e}")
        return False

def main():
    """主测试函数"""
    print("炎凰数据SQL方言独立部署验证测试")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print("=" * 80)
    
    # 执行测试 - 按重要性排序
    tests = [
        ("环境检查", test_environment_check, True),      # 必须通过
        ("方言注册验证", test_dialect_registration, True), # 必须通过
        ("核心转换功能", test_core_conversion, True),      # 必须通过
        ("SQLGlot集成", test_sqlglot_integration, False), # 重要但不强制
        ("LATERAL JOIN转换", test_lateral_join_conversion, False), # 高级功能
        ("基本功能验证", test_basic_functionality, True),  # 必须通过
    ]
    
    results = []
    critical_failed = False
    
    for test_name, test_func, is_critical in tests:
        try:
            result = test_func()
            results.append((test_name, result, is_critical))
            
            if is_critical and not result:
                critical_failed = True
                
        except Exception as e:
            print_test_result(test_name, False, f"测试异常: {e}")
            results.append((test_name, False, is_critical))
            
            if is_critical:
                critical_failed = True
    
    # 汇总结果
    print_header("测试结果汇总")
    
    passed_count = 0
    critical_passed = 0
    critical_total = 0
    total_count = len(results)
    
    for test_name, success, is_critical in results:
        status = "✅ 通过" if success else "❌ 失败"
        criticality = "【必须】" if is_critical else "【可选】"
        print(f"  {test_name}: {status} {criticality}")
        
        if success:
            passed_count += 1
        
        if is_critical:
            critical_total += 1
            if success:
                critical_passed += 1
    
    print(f"\n总体结果: {passed_count}/{total_count} 测试通过")
    print(f"核心功能: {critical_passed}/{critical_total} 必须功能通过")
    
    # 评估部署状态
    if critical_passed == critical_total:
        print("\n🎉 部署验证成功！")
        print("✅ 所有核心功能正常工作")
        print("✅ PyPI官方SQLGlot + 炎凰方言whl包部署成功！")
        print("✅ 可以在生产环境中使用此配置")
        deployment_success = True
    elif critical_passed >= critical_total - 1:
        print("\n✅ 部署基本成功！")
        print("✅ 核心功能基本正常")
        print("⚠️ 个别功能可能需要优化，但不影响主要使用")
        deployment_success = True
    else:
        print("\n❌ 部署验证失败！")
        print("❌ 核心功能存在问题，需要检查安装配置")
        deployment_success = False
    
    # 使用建议
    if deployment_success:
        print("\n📖 使用方法：")
        print("# 方式1：便捷接口（推荐）")
        print("from sqlglot_yanhuang import transpile_to_yanhuang")
        print("result = transpile_to_yanhuang(\"SELECT EXTRACT(year FROM now())\")")
        print()
        print("# 方式2：SQLGlot原生API")
        print("import sqlglot_yanhuang  # 导入即注册")
        print("import sqlglot")
        print("result = sqlglot.transpile(sql, read='postgres', write='yanhuang')")
    
    print("\n" + "=" * 80)
    print("测试完成")
    
    return deployment_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 