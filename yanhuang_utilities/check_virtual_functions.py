#!/usr/bin/env python3
"""
检查实际的虚继承函数列表并与函数支持矩阵对比
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlglot.dialects.yanhuang import Yanhuang
from yanhuang_utilities.yanhuang_function_support_matrix import YanhuangFunctionMatrix

def get_actual_virtual_functions():
    """获取实际的虚继承函数列表"""
    virtual_funcs = []
    
    # 检查Parser中的虚继承函数
    for name, cls in Yanhuang.Parser.FUNCTION_PARSERS.items():
        if hasattr(cls, '__name__') and cls.__module__ != 'sqlglot.dialects.yanhuang':
            virtual_funcs.append(name.upper())
    
    return sorted(list(set(virtual_funcs)))

def analyze_virtual_functions_with_matrix():
    """使用函数支持矩阵分析虚继承函数"""
    virtual_functions = get_actual_virtual_functions()
    matrix = YanhuangFunctionMatrix()
    
    print("🔍 实际虚继承函数分析")
    print("=" * 60)
    print(f"虚继承函数总数: {len(virtual_functions)}")
    
    # 使用矩阵验证
    validation_results = matrix.validate_virtual_inheritance_optimization(virtual_functions)
    recommendations = matrix.generate_optimization_recommendations(virtual_functions)
    
    print(f"\n📊 分析结果:")
    for category, functions in recommendations.items():
        print(f"   {category}: {len(functions)} 个")
    
    print(f"\n✅ 支持的函数 ({len(recommendations['can_inherit'])} 个):")
    for i, func in enumerate(recommendations['can_inherit']):
        print(f"{func:15}", end="")
        if (i + 1) % 6 == 0:
            print()
    if len(recommendations['can_inherit']) % 6 != 0:
        print()
    
    print(f"\n❌ 需要错误处理的函数 ({len(recommendations['need_error_handling'])} 个):")
    for i, func in enumerate(recommendations['need_error_handling']):
        print(f"{func:15}", end="")
        if (i + 1) % 6 == 0:
            print()
    if len(recommendations['need_error_handling']) % 6 != 0:
        print()
    
    print(f"\n⚠️ 需要映射的函数 ({len(recommendations['need_mapping'])} 个):")
    for func in recommendations['need_mapping']:
        print(f"   {func}")
    
    print(f"\n❓ 需要验证的函数 ({len(recommendations['need_verification'])} 个):")
    for func in recommendations['need_verification']:
        print(f"   {func}")
    
    # 优化潜力分析
    optimizable = len(recommendations['can_inherit']) + len(recommendations['need_mapping'])
    total = len(virtual_functions)
    print(f"\n💎 优化效果:")
    print(f"   可优化函数: {optimizable}/{total} ({optimizable/total*100:.1f}%)")
    print(f"   预计减少虚继承函数: {optimizable} 个")
    print(f"   优化后虚继承函数数量: {total - optimizable} 个")
    
    return virtual_functions, recommendations

def main():
    """主函数"""
    print("🔍 炎凰数据虚继承函数实际分析")
    print("=" * 80)
    
    virtual_functions, recommendations = analyze_virtual_functions_with_matrix()
    
    print(f"\n🎯 下一步优化建议:")
    print(f"   1. 优先处理 {len(recommendations['can_inherit'])} 个可直接继承的函数")
    print(f"   2. 为 {len(recommendations['need_error_handling'])} 个不支持的函数添加错误处理")
    print(f"   3. 为 {len(recommendations['need_mapping'])} 个函数添加映射转换")
    print(f"   4. 手动验证 {len(recommendations['need_verification'])} 个未知函数")

if __name__ == "__main__":
    main() 