# 炎凰数据 SQL 方言包

[![PyPI version](https://badge.fury.io/py/sqlglot-yanhuang-dialect.svg)](https://badge.fury.io/py/sqlglot-yanhuang-dialect)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

炎凰数据 SQL 方言包是 [SQLGlot](https://github.com/tobymao/sqlglot) 的扩展，提供完整的 PostgreSQL 到炎凰数据的 SQL 转换支持。

## 🚀 主要功能

- **PostgreSQL 到炎凰数据的 SQL 语法转换**：支持完整的语法映射
- **函数映射和优化**：120+ 函数自动映射转换
- **LATERAL JOIN 到 APPLY 转换**：智能处理复杂查询结构
- **完整的兼容性支持**：126+ 项功能测试覆盖
- **企业级稳定性**：100% 测试通过率

## 📦 安装

```bash
pip install sqlglot-yanhuang-dialect
```

## 🎯 快速开始

### 基本使用

```python
from sqlglot_yanhuang import transpile_to_yanhuang

# PostgreSQL 到炎凰数据转换
pg_sql = """
    SELECT u.user_id, u.email, loc.country 
    FROM users u 
    LEFT JOIN LATERAL (
        SELECT ip_location(u.ip_address) AS country
    ) loc ON true
"""

yanhuang_sql = transpile_to_yanhuang(pg_sql)
print(yanhuang_sql)
# 输出：SELECT u.user_id, u.email, loc.country 
#      FROM users u 
#      OUTER APPLY (SELECT IP_LOCATION(u.ip_address) AS country) loc
```

### 高级功能

```python
from sqlglot_yanhuang import parse_yanhuang
import sqlglot

# 解析炎凰数据 SQL
ast = parse_yanhuang("SELECT ARRAY_LENGTH(ARRAY[1,2,3])")

# 使用 SQLGlot 直接转换
result = sqlglot.transpile(
    "SELECT EXTRACT(year FROM created_at)",
    read="postgres", 
    write="yanhuang"
)[0]
print(result)  # SELECT DATE_PART('year', created_at)
```

## 🔧 支持的转换

### 函数映射
- `EXTRACT()` → `DATE_PART()`
- `CURRENT_TIMESTAMP` → `NOW()`
- `ARRAY_TO_STRING()` → `ARRAY_JOIN()`
- `CARDINALITY()` → `ARRAY_LENGTH()`
- 120+ 更多函数映射...

### 语法转换
- `LEFT JOIN LATERAL` → `OUTER APPLY`
- `INNER JOIN LATERAL` → `CROSS APPLY`
- `||` 字符串连接 → `CONCAT()`
- `~` 正则匹配 → `REGEXP_LIKE()`
- `::` 类型转换 → `CAST()`

### 高级功能
- PostgreSQL HINT 智能处理
- JSON 函数映射
- 窗口函数兼容
- CTE 语法支持

## 📊 兼容性

| 功能类别 | 支持度 | 测试覆盖 |
|---------|--------|----------|
| 基础语法 | 100% | ✅ |
| 函数映射 | 120+ 函数 | ✅ |
| LATERAL JOIN | 100% | ✅ |
| 复杂查询 | 95%+ | ✅ |

## 🧪 测试

```bash
# 运行测试
pytest tests/

# 运行特定测试
pytest tests/test_yanhuang_comprehensive.py -v
```

## 📚 文档

- [完整文档](https://docs.yanhuangdata.com/sqlglot-dialect)
- [API 参考](https://docs.yanhuangdata.com/sqlglot-dialect/api)
- [迁移指南](https://docs.yanhuangdata.com/sqlglot-dialect/migration)

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🔗 相关链接

- [炎凰数据官网](https://www.yanhuangdata.com)
- [SQLGlot 项目](https://github.com/tobymao/sqlglot)
- [问题反馈](https://github.com/yanhuangdata/sqlglot-yanhuang-dialect/issues)
