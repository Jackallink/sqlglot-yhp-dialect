"""
SQLGlot版本兼容性处理模块
=======================

处理不同SQLGlot版本之间的表达式类型差异，确保炎凰方言包在各个SQLGlot版本中都能正常工作。
"""

import sqlglot.expressions as exp
import warnings


def ensure_expression_compatibility():
    """确保表达式类型的兼容性
    
    处理不同SQLGlot版本中可能缺失的表达式类型，提供向后兼容性。
    """
    
    # 检查并创建可能缺失的表达式类型
    missing_expressions = []
    
    # 检查TimeStrLiteral是否存在
    if not hasattr(exp, 'TimeStrLiteral'):
        # 如果不存在，创建一个兼容的类
        class TimeStrLiteral(exp.Literal):
            """时间字符串字面量的兼容性类"""
            pass
        
        # 动态添加到expressions模块
        setattr(exp, 'TimeStrLiteral', TimeStrLiteral)
        missing_expressions.append('TimeStrLiteral')
    
    # 检查其他可能缺失的表达式类型
    expression_compat_map = {
        'DateStrLiteral': exp.Literal,
        'TimestampStrLiteral': exp.Literal,
        'TimeToTimeStr': getattr(exp, 'TimeToStr', exp.Func),
        'UnixToTimeStr': getattr(exp, 'UnixToStr', exp.Func),
    }
    
    for expr_name, base_class in expression_compat_map.items():
        if not hasattr(exp, expr_name):
            # 创建兼容类
            compat_class = type(expr_name, (base_class,), {
                '__doc__': f'{expr_name}兼容性类'
            })
            setattr(exp, expr_name, compat_class)
            missing_expressions.append(expr_name)
    
    # 如果有缺失的表达式，记录兼容性信息
    if missing_expressions:
        warnings.warn(
            f"SQLGlot版本兼容性: 自动添加了缺失的表达式类型: {', '.join(missing_expressions)}。"
            f"这确保了炎凰方言包在不同SQLGlot版本中的兼容性。",
            UserWarning,
            stacklevel=3
        )


def get_sqlglot_version_info():
    """获取SQLGlot版本信息"""
    import sqlglot
    
    version = getattr(sqlglot, '__version__', 'Unknown')
    
    # 检查关键表达式类型的存在
    expression_checks = {
        'TimeStrLiteral': hasattr(exp, 'TimeStrLiteral'),
        'TimeStrToTime': hasattr(exp, 'TimeStrToTime'),
        'TimeStrToDate': hasattr(exp, 'TimeStrToDate'),
        'TimeToTimeStr': hasattr(exp, 'TimeToTimeStr'),
        'UnixToTimeStr': hasattr(exp, 'UnixToTimeStr'),
    }
    
    return {
        'version': version,
        'expression_support': expression_checks
    }


def check_version_compatibility():
    """检查版本兼容性并返回报告"""
    version_info = get_sqlglot_version_info()
    
    compatibility_report = {
        'sqlglot_version': version_info['version'],
        'compatible': True,
        'issues': [],
        'recommendations': []
    }
    
    # 检查缺失的表达式类型
    missing_expressions = [
        expr_name for expr_name, exists in version_info['expression_support'].items()
        if not exists
    ]
    
    if missing_expressions:
        compatibility_report['issues'].append(
            f"缺失表达式类型: {', '.join(missing_expressions)}"
        )
        compatibility_report['recommendations'].append(
            "已自动添加兼容性类，无需手动处理"
        )
    
    # 检查版本范围
    version = version_info['version']
    if version != 'Unknown':
        try:
            # 解析版本号
            version_parts = version.split('.')
            major = int(version_parts[0]) if version_parts else 0
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            
            # 检查推荐版本范围
            if major < 25:
                compatibility_report['issues'].append(
                    f"SQLGlot版本过旧: {version}，推荐使用25.0+版本"
                )
                compatibility_report['recommendations'].append(
                    "考虑升级SQLGlot: pip install --upgrade sqlglot"
                )
            elif major > 30:
                compatibility_report['issues'].append(
                    f"SQLGlot版本较新: {version}，可能存在未知兼容性问题"
                )
                compatibility_report['recommendations'].append(
                    "如遇到问题，请报告给炎凰方言包开发团队"
                )
                
        except ValueError:
            compatibility_report['issues'].append(
                f"无法解析SQLGlot版本号: {version}"
            )
    
    # 如果有问题，标记为不完全兼容
    if compatibility_report['issues']:
        compatibility_report['compatible'] = False
    
    return compatibility_report


def apply_compatibility_fixes():
    """应用所有兼容性修复"""
    
    # 确保表达式兼容性
    ensure_expression_compatibility()
    
    # 可以在这里添加更多兼容性修复
    # 例如：函数签名变化、方法重命名等
    
    return get_sqlglot_version_info()


# 模块导入时自动应用兼容性修复
try:
    apply_compatibility_fixes()
except Exception as e:
    warnings.warn(
        f"应用SQLGlot兼容性修复时出错: {e}。可能影响炎凰方言包的功能。",
        UserWarning,
        stacklevel=2
    ) 