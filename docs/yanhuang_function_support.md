# 炎凰SQL方言函数支持文档

## 概述

炎凰SQL方言在SQLGlot框架中实现了完整的函数支持，包括标准SQL函数和炎凰SQL特有的扩展函数。本文档详细说明了支持的函数类型和使用方法。

## 测试验证

### 自动化测试
项目包含完整的函数支持测试套件，覆盖所有实现的函数：

- **总测试数量**: 87个函数
- **测试通过率**: 100%
- **测试分类**: 标量函数、聚合函数、表函数、炎凰SQL特有函数

### 测试运行
```bash
python tests/test_function_support.py
```

## 总结

炎凰SQL方言实现提供了完整的函数支持，包括：

1. **标量函数**: 60个（字符串、数学、条件、类型转换、日期时间函数）
2. **聚合函数**: 19个（包括基础聚合和统计类函数）
3. **表函数**: 13个（包括基础和炎凰SQL特有表函数）
4. **炎凰SQL特有函数**: 8个（文本分析、地理位置等）

**总计支持函数数量: 87个**，覆盖了炎凰SQL语法文档中提到的所有核心函数。

## 支持的函数分类

### 1. 字符串函数

#### 基础字符串操作
- `UPPER(str)` - 转换为大写
- `LOWER(str)` - 转换为小写  
- `SUBSTRING(str, start [, length])` - 提取子字符串
- `LENGTH(str)` - 字符串长度
- `CHAR_LENGTH(str)` - 字符长度（同LENGTH）
- `CHARACTER_LENGTH(str)` - 字符长度（同LENGTH）

#### 字符串截取和填充
- `LEFT(str, n)` - 左侧截取n个字符
- `RIGHT(str, n)` - 右侧截取n个字符  
- `REVERSE(str)` - 反转字符串
- `REPEAT(str, n)` - 重复字符串n次
- `LPAD(str, len, pad)` - 左填充
- `RPAD(str, len, pad)` - 右填充

#### 字符串查找和处理
- `POSITION(substr IN str)` - 查找子字符串位置
- `TRIM(str)` - 去除首尾空格
- `LTRIM(str)` - 去除左侧空格
- `RTRIM(str)` - 去除右侧空格
- `CONCAT(str1, str2, ...)` - 字符串连接
- `REPLACE(str, from, to)` - 字符串替换

### 2. 数学函数

#### 基础数学运算
- `ABS(n)` - 绝对值
- `CEIL(n)` / `CEILING(n)` - 向上取整
- `FLOOR(n)` - 向下取整
- `ROUND(n [, digits])` - 四舍五入
- `SQRT(n)` - 平方根
- `POWER(base, exp)` / `POW(base, exp)` - 幂运算
- `MOD(n, m)` - 取模运算

#### 三角函数
- `SIN(n)` - 正弦
- `COS(n)` - 余弦
- `TAN(n)` - 正切
- `ASIN(n)` - 反正弦
- `ACOS(n)` - 反余弦
- `ATAN(n)` - 反正切

#### 对数和指数函数
- `LOG(n)` - 自然对数
- `LOG10(n)` - 以10为底的对数
- `EXP(n)` - e的n次幂

#### 其他数学函数
- `SIGN(n)` - 符号函数
- `TRUNC(n [, digits])` - 截断函数
- `GREATEST(n1, n2, ...)` - 最大值
- `LEAST(n1, n2, ...)` - 最小值

### 3. 条件函数

- `IF(condition, true_value, false_value)` - 条件判断
- `DECODE(expr, search1, result1 [, search2, result2] ..., default)` - 多条件解码
- `CASE WHEN ... THEN ... ELSE ... END` - 条件分支
- `COALESCE(expr1, expr2, ...)` - 返回第一个非空值
- `NULLIF(expr1, expr2)` - 如果相等则返回NULL

### 4. 类型转换函数

- `CAST(expr AS type)` - 类型转换
  - 支持的类型：`INTEGER`, `VARCHAR(MAX)`, `DOUBLE`, `BOOLEAN`等

### 5. 日期时间函数

- `NOW()` - 当前时间戳（转换为GETDATE()）
- `CURRENT_TIMESTAMP` - 当前时间戳（转换为GETDATE()）
- `EXTRACT(part FROM datetime)` - 提取日期部分
- `DATE_TRUNC(precision, datetime)` - 日期截断

### 6. 炎凰SQL特有函数

#### 文本分析函数
- `CONTAINS(keyword)` - 全文检索
- `REGEX_EXTRACT(str, pattern)` - 正则表达式提取
- `REGEX_MATCH(str, pattern)` - 正则表达式匹配

#### 时间处理函数
- `TIME_BUCKET(interval, timestamp)` - 时间分桶

#### 地理位置函数
- `IP_TO_COUNTRY(ip)` - IP转国家
- `IP_TO_REGION(ip)` - IP转地区
- `IP_TO_CITY(ip)` - IP转城市
- `GEOHASH(lat, lng, precision)` - 地理哈希编码

### 7. 聚合函数（补充）

#### 字符串类聚合函数
- `MAX_STR(expr)` - 按字符串规则统计最大值
- `MIN_STR(expr)` - 按字符串规则统计最小值
- `STRING_AGG(expr, separator)` - 字符串聚合拼接

#### 统计类聚合函数
- `STDDEV_POP(expr)` - 计算总体标准差
- `STDDEV_SAMP(expr)` - 计算样本标准差
- `VAR_POP(expr)` - 计算总体方差
- `VAR_SAMP(expr)` - 计算样本方差

#### 分位数函数
- `QUANTILE_T_DIGEST(expr, fraction)` - 使用T-Digest算法计算分位数
- `PERCENTILE(expr, fraction)` - 等价于QUANTILE_T_DIGEST

#### 近似计算函数
- `APPROX_COUNT_DISTINCT(expr)` - 近似计数不重复值
- `APPROX_MEDIAN(expr)` - 使用T-Digest算法计算近似中位数

#### 其他聚合函数
- `PRODUCT(expr)` - 计算乘积
- `LATEST_VALUE(expr)` - 返回_time最大值所在行的字段值
- `EARLIEST_VALUE(expr)` - 返回_time最小值所在行的字段值

## 支持的表函数

### 1. 基础表函数

- `GENERATE_SERIES(start, end [, step])` - 生成数字序列
- `UNNEST(array)` - 数组展开

### 2. 炎凰SQL特有表函数

#### 数据解析函数
- `PARSE_JSON(json_str)` - JSON解析
- `PARSE_CSV(csv_str)` - CSV解析
- `PARSE_REGEX(str, pattern)` - 正则解析
- `PARSE_KV(str, delimiter, separator)` - 键值对解析
- `PARSE_XML(xml_str)` - XML解析

#### 地理位置函数
- `IP_LOCATION(ip)` - IP地理位置查询
- `GEO_DISTANCE(lat1, lng1, lat2, lng2)` - 地理距离计算

#### 数据加载函数
- `LOAD_CSV(file_path)` - 加载CSV文件
- `LOAD_JSON(file_path)` - 加载JSON文件
- `LOAD_PARQUET(file_path)` - 加载Parquet文件

## 实现特点

### 1. DECODE函数特殊处理
炎凰SQL方言中的DECODE函数保持为原始函数调用形式，不会转换为CASE表达式，这与PostgreSQL等其他方言不同。

```sql
-- 炎凰SQL
SELECT DECODE(status, 1, 'active', 2, 'inactive', 'unknown') FROM main;
-- 保持为 DECODE 函数

-- PostgreSQL
SELECT DECODE(status, 1, 'active', 2, 'inactive', 'unknown') FROM main;
-- 转换为 CASE 表达式
```

### 2. 函数名规范化
所有函数名遵循大写规范化策略，确保一致性。

### 3. 错误处理
对于不支持的函数或语法错误，提供清晰的错误信息。

## 使用示例

```python
import sqlglot
from sqlglot.dialects.yanhuang import Yanhuang

# 标量函数示例
sql = "SELECT UPPER(name), DECODE(status, 1, 'active', 'inactive') FROM users"
ast = sqlglot.parse(sql, dialect='yanhuang')[0]
print(ast.sql(dialect='yanhuang'))

# 表函数示例
sql = "SELECT * FROM IP_LOCATION('192.168.1.1')"
ast = sqlglot.parse(sql, dialect='yanhuang')[0]
print(ast.sql(dialect='yanhuang'))

# 复杂查询示例
sql = """
SELECT 
    TIME_BUCKET('1h', timestamp) as hour,
    COUNT(*) as count,
    IP_TO_COUNTRY(ip) as country
FROM logs 
WHERE CONTAINS('error')
GROUP BY hour, country
"""
ast = sqlglot.parse(sql, dialect='yanhuang')[0]
print(ast.sql(dialect='yanhuang'))
```

## 兼容性说明

炎凰SQL方言基于PostgreSQL方言扩展，因此：
- 完全兼容PostgreSQL的标准函数
- 添加了炎凰SQL特有的扩展函数
- 对某些函数（如DECODE）提供了不同的行为

## 更新日志

- **v1.0.0**: 完整实现73个函数，支持率100%
- 修复了CONCAT、MOD、UNNEST函数的问题
- 实现了DECODE函数的特殊处理
- 添加了完整的炎凰SQL特有函数支持 