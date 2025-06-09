"""
炎凰数据 SQL 方言包
=================

提供 SQLGlot 的炎凰数据方言支持，实现 PostgreSQL 到炎凰数据的 SQL 转换。

主要功能：
- PostgreSQL 到炎凰数据的 SQL 语法转换
- 函数映射和优化
- LATERAL JOIN 到 APPLY 转换
- 完整的兼容性支持

使用示例：
    from sqlglot_yanhuang import transpile_to_yanhuang
    
    result = transpile_to_yanhuang(
        "SELECT * FROM users u LEFT JOIN LATERAL (SELECT count(*) FROM orders WHERE user_id = u.id) o ON true"
    )
    print(result)  # PostgreSQL LATERAL JOIN 转换为炎凰数据 OUTER APPLY
"""

__version__ = "1.0.0"
__author__ = "炎凰数据团队"

import sqlglot
import sqlglot.dialects

# 导入兼容性模块（自动应用兼容性修复）
from . import compatibility

# 导入炎凰数据方言
from .dialects.yanhuang import Yanhuang

# 动态注册炎凰方言到SQLGlot
def _register_yanhuang_dialect():
    """动态注册炎凰方言到SQLGlot"""
    try:
        # 方法1：通过dialects模块注册
        if hasattr(sqlglot.dialects, '__dict__'):
            sqlglot.dialects.__dict__['yanhuang'] = Yanhuang
        
        # 方法2：通过内部注册机制
        if hasattr(sqlglot, '_dialects'):
            sqlglot._dialects['yanhuang'] = Yanhuang
        
        # 方法3：直接设置到sqlglot模块
        if not hasattr(sqlglot, 'yanhuang'):
            setattr(sqlglot, 'yanhuang', Yanhuang)
            
        # 方法4：尝试使用可能存在的注册API
        if hasattr(sqlglot, 'register_dialect'):
            sqlglot.register_dialect('yanhuang', Yanhuang)
        
        return True
    except Exception as e:
        import warnings
        warnings.warn(f"炎凰方言注册失败: {e}")
        return False

# 执行注册
_registration_success = _register_yanhuang_dialect()

def transpile_to_yanhuang(sql, source_dialect="postgres"):
    """
    将 SQL 转换为炎凰数据方言
    
    Args:
        sql (str): 源 SQL 语句
        source_dialect (str): 源方言，默认为 postgres
    
    Returns:
        str: 转换后的炎凰数据 SQL
    """
    try:
        return sqlglot.transpile(sql, read=source_dialect, write="yanhuang")[0]
    except Exception as e:
        # 如果标准方式失败，尝试直接实例化
        try:
            parser = Yanhuang.Parser()
            generator = Yanhuang.Generator()
            
            # 解析SQL
            if source_dialect == "postgres":
                from sqlglot.dialects.postgres import Postgres
                source_parser = Postgres.Parser()
            else:
                source_parser = sqlglot.Parser()
            
            ast = source_parser.parse(sql)[0]
            
            # 生成炎凰SQL
            return generator.sql(ast)
        except Exception as inner_e:
            raise Exception(f"SQL转换失败: {e}, 备用方案也失败: {inner_e}")

def parse_yanhuang(sql):
    """
    解析炎凰数据 SQL
    
    Args:
        sql (str): 炎凰数据 SQL 语句
    
    Returns:
        Expression: 解析后的 AST
    """
    try:
        return sqlglot.parse_one(sql, dialect="yanhuang")
    except Exception:
        # 如果标准方式失败，直接使用炎凰解析器
        parser = Yanhuang.Parser()
        return parser.parse(sql)[0]

def check_registration():
    """检查方言注册状态"""
    checks = []
    
    # 检查1：SQLGlot是否识别yanhuang方言
    try:
        sqlglot.transpile("SELECT 1", read="postgres", write="yanhuang")
        checks.append("✅ SQLGlot直接识别yanhuang方言")
    except Exception as e:
        checks.append(f"❌ SQLGlot不识别yanhuang方言: {e}")
    
    # 检查2：便捷函数是否工作
    try:
        result = transpile_to_yanhuang("SELECT 1")
        checks.append("✅ transpile_to_yanhuang函数工作正常")
    except Exception as e:
        checks.append(f"❌ transpile_to_yanhuang函数失败: {e}")
    
    # 检查3：解析函数是否工作
    try:
        ast = parse_yanhuang("SELECT 1")
        checks.append("✅ parse_yanhuang函数工作正常")
    except Exception as e:
        checks.append(f"❌ parse_yanhuang函数失败: {e}")
    
    return checks

def check_compatibility():
    """检查SQLGlot版本兼容性"""
    return compatibility.check_version_compatibility()

def get_version_info():
    """获取详细的版本信息"""
    import sqlglot
    
    return {
        'yanhuang_dialect_version': __version__,
        'sqlglot_version': getattr(sqlglot, '__version__', 'Unknown'),
        'compatibility_info': compatibility.get_sqlglot_version_info(),
        'registration_status': check_registration()
    }

__all__ = ["transpile_to_yanhuang", "parse_yanhuang", "Yanhuang", "check_registration", "check_compatibility", "get_version_info"]
