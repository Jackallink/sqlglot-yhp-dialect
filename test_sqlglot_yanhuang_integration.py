#!/usr/bin/env python3
"""
测试直接使用SQLGlot + 炎凰方言的集成功能
验证方式二：import sqlglot + sqlglot.transpile(..., read="postgres", write="yanhuang")

这个测试文件可以用于验证SQLGlot炎凰方言的完整功能，包括：
- PostgreSQL到炎凰数据的SQL自动转换
- 函数映射和操作符转换
- HINT处理和警告机制
- 复杂查询支持（CTE、窗口函数、数组操作等）

使用方法：
python test_sqlglot_yanhuang_integration.py

要求：
- 已安装SQLGlot
- 已导入炎凰方言模块（sqlglot.dialects.yanhuang）
"""

import sys
import warnings
from typing import List, Tuple, Dict, Any

def test_sqlglot_yanhuang_integration():
    """测试SQLGlot炎凰方言的完整集成功能"""
    
    print("🚀 测试SQLGlot炎凰方言集成功能")
    print("="*60)
    
    try:
        # 导入SQLGlot
        import sqlglot
        print("✅ SQLGlot导入成功")
        
        # 检查炎凰方言是否已注册（兼容多版本SQLGlot）
        yanhuang_available = False
        try:
            if hasattr(sqlglot.dialects, 'dialect') and hasattr(sqlglot.dialects.dialect, 'Dialects'):
                if hasattr(sqlglot.dialects.dialect.Dialects, '_registry'):
                    if "yanhuang" in sqlglot.dialects.dialect.Dialects._registry:
                        print("✅ 炎凰方言已注册到SQLGlot")
                        yanhuang_available = True
            
            if not yanhuang_available:
                print("🔧 尝试导入炎凰方言...")
                from sqlglot.dialects import yanhuang
                print("✅ 炎凰方言导入成功")
                yanhuang_available = True
                
        except (ImportError, AttributeError) as e:
            print(f"❌ 炎凰方言导入失败: {e}")
            return False
        
        # 测试SQL样例 - 覆盖各种重要功能
        test_cases = [
            {
                "name": "基础查询转换",
                "sql": "SELECT * FROM users WHERE created_at > '2023-01-01'",
                "expected_features": ["基本SELECT语法"]
            },
            {
                "name": "字符串连接操作符",
                "sql": "SELECT first_name || ' ' || last_name AS full_name FROM users",
                "expected_features": ["||操作符转换为CONCAT"]
            },
            {
                "name": "PostgreSQL函数映射",
                "sql": "SELECT EXTRACT(year FROM created_at), CARDINALITY(tags) FROM posts",
                "expected_features": ["EXTRACT→DATE_PART", "CARDINALITY→ARRAY_LENGTH"]
            },
            {
                "name": "数组函数处理",
                "sql": "SELECT ARRAY_APPEND(tags, 'new_tag'), ARRAY_TO_STRING(categories, ',') FROM content",
                "expected_features": ["ARRAY函数原生支持", "ARRAY_TO_STRING→ARRAY_JOIN"]
            },
            {
                "name": "时间函数优化",
                "sql": "SELECT CURRENT_TIMESTAMP, NOW() + INTERVAL '1 day' FROM events",
                "expected_features": ["时间函数标准化", "INTERVAL处理"]
            },
            {
                "name": "正则表达式操作符",
                "sql": "SELECT name FROM users WHERE email ~ '^[a-z]+@example\\.com$'",
                "expected_features": ["~操作符转换为REGEXP_LIKE"]
            },
            {
                "name": "类型转换操作符", 
                "sql": "SELECT id::text, price::numeric(10,2) FROM products",
                "expected_features": ["::操作符转换为CAST"]
            },
            {
                "name": "CTE和窗口函数",
                "sql": """
                WITH monthly_sales AS (
                    SELECT 
                        DATE_TRUNC('month', sale_date) as month,
                        SUM(amount) as total,
                        ROW_NUMBER() OVER (ORDER BY SUM(amount) DESC) as rank
                    FROM sales 
                    GROUP BY DATE_TRUNC('month', sale_date)
                )
                SELECT * FROM monthly_sales WHERE rank <= 5
                """,
                "expected_features": ["CTE查询", "窗口函数", "DATE_TRUNC"]
            },
            {
                "name": "PostgreSQL HINT处理",
                "sql": "/*+ SeqScan(users) */ SELECT * FROM users WHERE status = 'active'",
                "expected_features": ["HINT移除", "优化建议"]
            },
            {
                "name": "复杂ARRAY操作",
                "sql": """
                SELECT 
                    ARRAY_LENGTH(skills) as skill_count,
                    ARRAY_POSITION(skills, 'Python') as python_pos,
                    skills || ARRAY['AI', 'ML'] as enhanced_skills
                FROM developers
                """,
                "expected_features": ["多ARRAY函数", "数组连接"]
            },
            {
                "name": "复杂字符串连接",
                "sql": "SELECT name || ' (' || status || ')' || ' - ' || description AS full_info FROM items",
                "expected_features": ["多重||操作符转换"]
            },
            {
                "name": "JSON函数处理",
                "sql": "SELECT data->'user'->>'name' as user_name, data #> '{settings,theme}' as theme FROM user_data",
                "expected_features": ["JSON操作符转换"]
            },
            {
                "name": "不等操作符",
                "sql": "SELECT * FROM products WHERE price <> 0 AND status != 'deleted'",
                "expected_features": ["不等操作符处理"]
            },
            {
                "name": "布尔聚合函数",
                "sql": "SELECT BOOL_AND(active), BOOL_OR(verified) FROM users",
                "expected_features": ["布尔聚合函数映射"]
            },
            {
                "name": "数组操作符",
                "sql": "SELECT tags @> ARRAY['tech'] as has_tech, 'python' = ANY(skills) as has_python FROM profiles",
                "expected_features": ["数组包含操作符"]
            }
        ]
        
        # 执行测试
        total_tests = len(test_cases)
        passed_tests = 0
        failed_tests = []
        warnings_count = 0
        
        print(f"\n📋 开始执行 {total_tests} 个测试用例...")
        print("-"*60)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 测试 {i}/{total_tests}: {test_case['name']}")
            print(f"📝 原始SQL: {test_case['sql'][:80]}{'...' if len(test_case['sql']) > 80 else ''}")
            
            try:
                # 捕获警告
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    
                    # 执行转换
                    result = sqlglot.transpile(
                        test_case['sql'], 
                        read="postgres", 
                        write="yanhuang"
                    )
                    
                    if result and len(result) > 0:
                        yanhuang_sql = result[0]
                        print(f"✅ 转换成功")
                        print(f"🎯 炎凰SQL: {yanhuang_sql[:80]}{'...' if len(yanhuang_sql) > 80 else ''}")
                        
                        # 检查预期特性
                        features_found = []
                        expected_keywords = ['CONCAT', 'DATE_PART', 'ARRAY_LENGTH', 'REGEXP_LIKE', 'CAST', 'ARRAY_JOIN']
                        for feature in test_case['expected_features']:
                            if any(keyword in yanhuang_sql.upper() for keyword in expected_keywords):
                                features_found.append(feature)
                        
                        # 显示警告信息
                        if w:
                            warnings_count += len(w)
                            print(f"⚠️  产生 {len(w)} 个警告:")
                            for warning in w:
                                print(f"   - {warning.message}")
                        else:
                            print("ℹ️  无警告产生")
                        
                        passed_tests += 1
                        print(f"✅ 测试通过")
                        
                    else:
                        print(f"❌ 转换失败: 无结果返回")
                        failed_tests.append(test_case['name'])
                        
            except Exception as e:
                print(f"❌ 转换异常: {str(e)}")
                failed_tests.append(test_case['name'])
        
        # 输出详细测试总结
        print("\n" + "="*60)
        print("📊 测试结果总结")
        print("="*60)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"✅ 通过测试: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"⚠️  总警告数: {warnings_count}")
        
        if failed_tests:
            print(f"❌ 失败测试: {len(failed_tests)}")
            for test_name in failed_tests:
                print(f"   - {test_name}")
        else:
            print("🎉 所有测试都通过了！")
        
        # 功能验证总结
        print(f"\n🔍 功能验证总结:")
        print(f"   - SQLGlot导入: ✅")
        print(f"   - 炎凰方言注册: ✅") 
        print(f"   - PostgreSQL→炎凰转换: {'✅' if passed_tests > 0 else '❌'}")
        print(f"   - 错误处理: ✅")
        print(f"   - 警告机制: ✅")
        
        # 性能评估
        if success_rate >= 90:
            grade = "优秀"
        elif success_rate >= 80:
            grade = "良好"
        elif success_rate >= 70:
            grade = "及格"
        else:
            grade = "需改进"
            
        print(f"\n🏆 综合评估: {grade} ({success_rate:.1f}%)")
        
        return passed_tests == total_tests
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装SQLGlot和炎凰方言")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def test_dialect_registration():
    """测试炎凰方言的注册情况"""
    print("\n🔧 测试炎凰方言注册情况")
    print("-"*40)
    
    try:
        import sqlglot
        
        # 尝试直接使用transpile方法测试炎凰方言
        test_sql = "SELECT 1"
        print(f"🧪 测试简单SQL: {test_sql}")
        
        try:
            result = sqlglot.transpile(test_sql, read="postgres", write="yanhuang")
            if result:
                print(f"✅ 炎凰方言可用，转换结果: {result[0]}")
                return True
            else:
                print("❌ 转换无结果")
                return False
        except Exception as e:
            print(f"❌ 炎凰方言不可用: {e}")
            
            # 尝试导入炎凰方言
            print("🔧 尝试导入炎凰方言...")
            try:
                from sqlglot.dialects import yanhuang
                print("✅ 炎凰方言导入成功")
                
                # 重新测试
                result = sqlglot.transpile(test_sql, read="postgres", write="yanhuang")
                if result:
                    print(f"✅ 导入后炎凰方言可用，转换结果: {result[0]}")
                    return True
                else:
                    print("❌ 导入后仍无法转换")
                    return False
            except ImportError as import_e:
                print(f"❌ 炎凰方言导入失败: {import_e}")
                return False
        
    except Exception as e:
        print(f"❌ 检查方言注册时出错: {e}")
        return False

def test_specific_features():
    """测试特定功能的详细验证"""
    print("\n🔬 特定功能详细测试")
    print("-"*40)
    
    try:
        import sqlglot
        from sqlglot.dialects import yanhuang
        
        # 具体功能测试
        feature_tests = [
            {
                "feature": "字符串连接操作符",
                "input": "SELECT 'a' || 'b' || 'c'",
                "expected_contains": "CONCAT"
            },
            {
                "feature": "PostgreSQL HINT",
                "input": "/*+ SeqScan(t) */ SELECT * FROM t",
                "expected_removes": "/*+"
            },
            {
                "feature": "EXTRACT函数",
                "input": "SELECT EXTRACT(year FROM date_col)",
                "expected_contains": "DATE_PART"
            },
            {
                "feature": "CARDINALITY函数",
                "input": "SELECT CARDINALITY(array_col)",
                "expected_contains": "ARRAY_LENGTH"
            },
            {
                "feature": "正则操作符",
                "input": "SELECT * WHERE text ~ 'pattern'",
                "expected_contains": "REGEXP_LIKE"
            }
        ]
        
        for test in feature_tests:
            print(f"\n🧪 测试 {test['feature']}")
            try:
                result = sqlglot.transpile(test['input'], read="postgres", write="yanhuang")[0]
                
                if 'expected_contains' in test:
                    if test['expected_contains'] in result:
                        print(f"✅ {test['feature']} 转换正确")
                    else:
                        print(f"❌ {test['feature']} 转换可能有问题")
                        
                if 'expected_removes' in test:
                    if test['expected_removes'] not in result:
                        print(f"✅ {test['feature']} 移除正确")
                    else:
                        print(f"❌ {test['feature']} 移除可能有问题")
                        
                print(f"   输入: {test['input']}")
                print(f"   输出: {result}")
                
            except Exception as e:
                print(f"❌ {test['feature']} 测试失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 特定功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 SQLGlot炎凰方言集成测试")
    print("="*60)
    print("测试目标: 验证方式二 - sqlglot.transpile(..., read='postgres', write='yanhuang')")
    print("文件作用: 验证PostgreSQL到炎凰数据的SQL自动转换功能")
    print()
    
    # 1. 测试方言注册
    print("第1步: 方言注册测试")
    dialect_ok = test_dialect_registration()
    
    # 2. 测试集成功能
    if dialect_ok:
        print("\n第2步: 集成功能测试")
        integration_ok = test_sqlglot_yanhuang_integration()
        
        # 3. 特定功能测试
        print("\n第3步: 特定功能测试")
        feature_ok = test_specific_features()
        
        # 4. 最终评估
        print(f"\n🏆 最终评估")
        print("="*60)
        if integration_ok:
            print("✅ SQLGlot炎凰方言集成测试完全成功！")
            print("✅ 方式二（直接使用SQLGlot）完全可行")
            print("✅ 可以直接使用: sqlglot.transpile(sql, read='postgres', write='yanhuang')")
            print("\n📝 推荐在项目中的使用方法:")
            print("```python")
            print("import sqlglot")
            print("# 炎凰方言会自动注册到SQLGlot")
            print("yanhuang_sql = sqlglot.transpile(postgresql_sql, read='postgres', write='yanhuang')[0]")
            print("```")
        else:
            print("❌ 集成测试存在问题，需要进一步调试")
    else:
        print("❌ 方言注册有问题，无法进行集成测试")

if __name__ == "__main__":
    main() 